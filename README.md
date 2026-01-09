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
  
  