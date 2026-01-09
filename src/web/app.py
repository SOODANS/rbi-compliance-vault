import os
import sys

# --- SQLite Fix for Docker ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="RBI Compliance AI", page_icon="🏦", layout="wide")

with st.sidebar:
    st.header("⚙️ Response Settings")
    response_mode = st.radio(
        "Select Response Verbosity:",
        ["Detailed", "Brief"],
        index=0,
        help="Detailed provides full regulatory depth; Brief focuses on critical points."
    )

# --- 2. Dynamic Prompt Selection ---
if response_mode == "Brief":
    instruction_text = """
    1. Answer the question ONLY using the provided context. If the answer is not in the context, state that clearly.
    2. Provide a concise Executive Summary of the critical points first.
    3. Use bullet points for readability.
    4. PRIORITIZE NUMERIC LIMITS: Explicitly include aggregate loan limits (e.g., ₹60,000), deposit caps (₹1 lakh), and validity timelines (e.g., 1 year).
    5. SECTOR SPECIFICITY: If limits differ between bank types (e.g., UCBs vs. Commercial Banks), highlight these differences.
    6. If a specific numeric limit/timeline is not mentioned, state: "The provided text does not specify the exact [amount/timeline]."
    7. Always cite the Source and Date clearly for each point."""
else:
    instruction_text = """
    1. Answer the question ONLY using the provided context. Do not use outside knowledge.
    2. Provide a comprehensive and thorough answer based on the context.
    3. Explain the regulatory rationale where available, especially for limits and timelines.
    4. GROUNDING RULE: You must extract and highlight all numeric values, such as the ₹60,000 sanction limit or the 1-year account validity for Aadhaar OTP accounts.
    5. SECTOR COMPARISON: Explicitly mention if the rules change for different bank categories (e.g., Payments Banks, SFBs, or UCBs).
    6. If specific technical thresholds are missing from the text, state: "The provided text does not specify the exact [amount/timeline]."
    7. Always cite the Source and Date clearly for each point."""

@st.cache_resource
def initialize_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    persist_directory = "/app/data/chroma_db"
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )
    
    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )
    
    # --- 3. Updated Prompt Template (Notice the double {{braces}}) ---
    # Python fills in {instruction_text} now.
    # LangChain will fill in {context} and {question} later because of the double {{ }}.
    template = f"""
    You are an expert RBI Compliance Officer. Use the provided context to answer the question.

    Context: {{context}}

    Instruction: 
    {instruction_text}

    Question: {{question}}
    Helpful Answer:"""

    # Now LangChain will correctly find 'context' and 'question' as input variables.
    QA_PROMPT = PromptTemplate(
        template=template, input_variables=["context", "question"]
    )
    
    # --- MODIFIED RETRIEVER ---
    # We use a custom document prompt to ensure metadata is visible to the LLM
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        #retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
        retriever = vector_db.as_retriever(
            search_type="mmr", # Ensures a diverse set of documents are retrieved
            search_kwargs={"k": 20, "fetch_k": 50} # Looks deeper into the database 
            # Increased from 15 to 20 & 30 t0 50 for better context coverage
        ),
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": QA_PROMPT,
            # This line is key: it tells LangChain how to format each chunk's metadata
            "document_prompt": PromptTemplate(
                input_variables=["page_content", "source", "date"],
                template="[SOURCE]: {source}\n[DATE]: {date}\n[CONTENT]: {page_content}"
            )
        }
    )
    
    return qa_chain

# --- UI Layout ---
st.title("🏦 RBI Compliance Chatbot")
st.markdown("Query the knowledge base of **316 Master Directions** with real-time citations.")

try:
    qa_engine = initialize_system()
except Exception as e:
    st.error(f"Failed to load system: {e}. Ensure chroma_db is initialized.")
    st.stop()

# --- 1. Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. Redraw History (CRITICAL STEP) ---
# This ensures old messages stay visible when the script reruns
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. Handle New User Input ---
if prompt := st.chat_input("Ask about KYC, FEMA, Digital Lending, etc..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching RBI Master Directions..."):
            response = qa_engine({"query": prompt})
            answer = response["result"]
            
            # --- FIX: Construct the full message including links for persistence ---
            citation_text = "\n\n**Verified Sources:**\n"
            unique_sources = set()
            for doc in response["source_documents"]:
                source_name = doc.metadata.get('title', 'RBI Master Direction')
                source_date = doc.metadata.get('date', 'Nov 28, 2025')
                source_url = doc.metadata.get('url')
                
                if source_url:
                    src_display = f"**{source_name}** (Dated: {source_date})"
                    if src_display not in unique_sources:
                        citation_text += f"- {src_display} [🔗 Read True Copy]({source_url})\n"
                        unique_sources.add(src_display)
            
            # Combine answer and citations into one message for session storage
            full_content = f"{answer}{citation_text}"
            
            # Display result
            st.markdown(full_content)
            
            # Keep the expander for visual neatness in the current turn if you prefer
            with st.expander("📚 View Summary of Sources"):
                for src in unique_sources:
                    st.write(f"- {src}")
                    
    # Save the FULL CONTENT (text + links) to history so it persists after Phase 2 redraw                        
    st.session_state.messages.append({"role": "assistant", "content": answer})