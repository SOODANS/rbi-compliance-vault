import os
import sys

# --- SQLite Fix for Docker (Must be at the very top) ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    print("pysqlite3-binary not found, using system sqlite3")
# ------------------------------------------------------

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from src.processor.chunking import RBIProcessor
from dotenv import load_dotenv

load_dotenv()

def initialize_vector_store():
    print("🚀 Starting Indexing Engine...")
    
    # 1. Setup Gemini Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # 2. Process PDFs using the logic in chunking.py
    processor = RBIProcessor()
    documents = processor.process_all_documents()

    if not documents:
        print("❌ No documents were processed. Check /app/data/raw_pdfs and metadata.csv")
        return

    # 3. Create Persistent Chroma Store
    persist_directory = "/app/data/chroma_db"
    
    print(f"📦 Creating index for {len(documents)} text chunks...")
    
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    # In newer Chroma versions, persist() is called automatically, 
    # but we include it for compatibility.
    print(f"✅ Success! Vector Database created at {persist_directory}")

if __name__ == "__main__":
    initialize_vector_store()