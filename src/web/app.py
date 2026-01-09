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
    
    # --- MODIFIED PROMPT TEMPLATE ---
    # We add instructions to specifically look at the metadata we injected
    template = """
    You are an expert RBI Compliance Officer. Use the provided context to answer the question.

    Context: {context}

    Instruction: 
    1. Provide a comprehensive answer based on the context.
    2. If multiple directions are mentioned, summarize the common requirements.
    3. Always cite the Source and Date clearly for each point.

    Question: {question}
    Helpful Answer:"""
    
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
            search_kwargs={"k": 10, "fetch_k": 20} # Looks deeper into the database
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
st.markdown("Query the knowledge base of **89 Master Directions** with real-time citations.")

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