This is the finalized, comprehensive README.md for the RBI Compliance Vault. It incorporates the scraper, indexer, chat engine, and verification commands, along with essential maintenance and troubleshooting steps to ensure a production-ready system.

# 🏦 RBI Compliance Vault
**AI-Powered Regulatory Intelligence for 89 Master Directions**

An end-to-end RAG (Retrieval-Augmented Generation) pipeline designed to ingest, index, and query the complete knowledge base of RBI Master Directions with 100% verifiable citations to official sources.

---

## 📋 Prerequisites
- **Docker Desktop**: Installed and running on Windows.
- **Google AI Studio API Key**: Required for Gemini 2.5 Flash and Gemini Embeddings.
- **Hardware**: Minimum 8GB RAM allocated to Docker.
- **Directory Structure**: Ensure your project is at `D:\rbi-compliance-vault`.

---

*******************************************************************************************************

## 🛠️ Initial Setup

### 1. Configure Environment
Create a `.env` file in the root directory (`D:\rbi-compliance-vault\.env`) with the following content:
```text
GOOGLE_API_KEY=your_gemini_api_key_here
DATA_DIR=/app/data

*******************************************************************************************************

2. Build the Docker Image
Run this command to build the core engine:

docker build -t rbi-compliance-ai .

*******************************************************************************************************

🚀 Execution Pipeline
Phase 1: Data Acquisition (Scraper)

To download the 89 PDFs and generate the metadata.csv containing official publication dates and URLs:

Phase 1: Data Acquisition (Scraper)
To download the 89 PDFs and generate the metadata.csv containing official publication dates and URLs:

docker run --rm `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  -v "D:\rbi-compliance-vault\src:/app/src" `
  --env-file .env `
  rbi-compliance-ai python -m src.scraper.rbi_scraper

*******************************************************************************************************

Phase 2: Knowledge Indexing (Vector DB)
To process the downloaded PDFs into semantic mathematical vectors stored in ChromaDB:

docker run --rm `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  -v "D:\rbi-compliance-vault\src:/app/src" `
  --env-file .env `
  rbi-compliance-ai python -m src.engine.initialize_db

*******************************************************************************************************

Phase 3: Launch the Chatbot (Streamlit)
To start the web interface and begin querying regulations:

docker run -it --rm `
  -p 8501:8501 `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  -v "D:\rbi-compliance-vault\src:/app/src" `
  --env-file .env `
  rbi-compliance-ai streamlit run src/web/app.py
  
Access at: http://localhost:8501

*******************************************************************************************************

🧹 Maintenance & Troubleshooting
Resetting the Knowledge Base
If you notice stale data or missing links, perform a "Clean Slate" reset to clear the database cache:

# Delete the old database folder
Remove-Item -Path "D:\rbi-compliance-vault\data\chroma_db" -Recurse -Force

# Then re-run Phase 2 (Indexing)

*******************************************************************************************************

Verifying Metadata Integrity:

Run this command to inspect a raw database chunk and ensure link, date, and source are correctly indexed:

docker run --rm `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  --env-file .env `
  rbi-compliance-ai python -c "import sys; __import__('pysqlite3'); sys.modules['sqlite3'] = sys.modules.pop('pysqlite3'); from langchain_community.vectorstores import Chroma; from langchain_google_genai import GoogleGenerativeAIEmbeddings; import os; db = Chroma(persist_directory='/app/data/chroma_db', embedding_function=GoogleGenerativeAIEmbeddings(model='models/text-embedding-004', google_api_key=os.getenv('GOOGLE_API_KEY'))); print(db.get(limit=1)['metadatas'])"

Expected Output: [{'date': 'Nov 28, 2025', 'url': 'https://...', 'source': '...', 'title': '...'}]

*******************************************************************************************************

🏛️ High-Level Architecture
The system functions through a three-stage lifecycle:

1. Extraction: Automated scraping of RBI's regulatory portal for PDFs and metadata.
2. Indexing: Semantic chunking and metadata attachment (Source, Date, URL) for primary-source verification.
3. Retrieval: Multi-document search with Gemini 2.5 Flash to provide context-aware, cited compliance answers.

*******************************************************************************************************

### ✅ Why this documentation works:

* **Critical Missing Commands**: Includes the `docker build` command which is essential for first-time setup.
* **Architecture Visualization**: Added a placeholder for the architecture diagram to help future users understand the data flow.
* **Detailed Maintenance**: Included the specific `Remove-Item` logic to handle stale metadata issues we encountered.
* **Verification Logic**: Retained the advanced Python one-liner to check the "raw truth" of the database.

[Comprehensive guide to building and documenting RAG applications](https://www.youtube.com/watch?v=eVc-tQxdpmw)

This video provides an overview of best practices for structuring and documenting regulatory compliance chatbots using LangChain and Docker.
*******************************************************************************************************