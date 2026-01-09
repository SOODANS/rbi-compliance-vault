# rbi-compliance-vault
RAG pipeline for RBI regulatory compliance using Gemini



#Run the Scrapper




#Run the Indexer
docker run --rm `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  -v "D:\rbi-compliance-vault\src:/app/src" `
  --env-file .env `
  rbi-compliance-ai python -m src.engine.initialize_db


#Run the ChatEngine
docker run -it --rm `
  -p 8501:8501 `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  -v "D:\rbi-compliance-vault\src:/app/src" `
  --env-file .env `
  rbi-compliance-ai streamlit run src/web/app.py
  
 
 
#Delete the old database folder to ensure no stale data remains
Remove-Item -Path "D:\rbi-compliance-vault\data\chroma_db" -Recurse -Force

#Verify the indexing
Run this in your PowerShell. It includes the environment file and the necessary code to swap the SQLite version at runtime to ensure compatibility with your Docker environment.

docker run --rm `
  -v "D:\rbi-compliance-vault\data:/app/data" `
  --env-file .env `
  rbi-compliance-ai python -c "import sys; __import__('pysqlite3'); sys.modules['sqlite3'] = sys.modules.pop('pysqlite3'); from langchain_community.vectorstores import Chroma; from langchain_google_genai import GoogleGenerativeAIEmbeddings; import os; db = Chroma(persist_directory='/app/data/chroma_db', embedding_function=GoogleGenerativeAIEmbeddings(model='models/text-embedding-004', google_api_key=os.getenv('GOOGLE_API_KEY'))); print(db.get(limit=1)['metadatas'])"
  
Sample Output: 

[{'date': 'Nov 28, 2025', 'source': 'Reserve Bank of India...', 'link': 'https://rbidocs.rbi.org.in/...', 'title': 'Reserve Bank of India...'}]