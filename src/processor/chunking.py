import os
import pandas as pd
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class RBIProcessor:
    def __init__(self):
        self.raw_dir = os.getenv("DATA_DIR", "./data/raw_pdfs")
        self.chunk_size = 1500  # Large enough for legal context
        self.chunk_overlap = 200 # Overlap to ensure continuity
        
        # Splitter that prioritizes newlines and sentences
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path):
        """Extracts text and maintains basic structure."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        return text

    def process_all_documents(self):
        """Processes all PDFs in the data directory and returns LangChain Documents."""
        all_chunks = []
        #metadata_df = pd.read_csv(os.path.join(self.raw_dir, "metadata.csv"))
        metadata_df = pd.read_csv("/app/data/metadata.csv") #Synchronization Fix

        for index, row in metadata_df.iterrows():
            #pdf_path = os.path.join(self.raw_dir, row['filename'])
            pdf_path = os.path.join(self.raw_dir, row['local_path']) #Synchronization Fix
            
            if not os.path.exists(pdf_path):
                continue

            print(f"Processing: {row['title']}")
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            # Create LangChain chunks with attached metadata
            chunks = self.splitter.split_text(raw_text)
            
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": row['title'],
                        "date": row['date'],
                        "link": row['url'],
                        "chunk_id": i
                    }
                )
                all_chunks.append(doc)
        
        return all_chunks

if __name__ == "__main__":
    processor = RBIProcessor()
    docs = processor.process_all_documents()
    print(f"Created {len(docs)} semantic chunks from RBI Master Directions.")