import os
import pandas as pd
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class RBIProcessor:
    def __init__(self):
        # Fallback to absolute path for Docker compatibility
        self.raw_dir = os.getenv("DATA_DIR", "/app/data/raw_pdfs")
        self.chunk_size = 1500
        self.chunk_overlap = 500
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path):
        """Extracts text using PyMuPDF."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text

    def process_all_documents(self):
        """Processes PDFs and returns metadata-enriched LangChain Documents."""
        all_chunks = []
        # Ensure path matches your Docker volume mount
        metadata_df = pd.read_csv("/app/data/metadata.csv")

        for _, row in metadata_df.iterrows():
            pdf_path = os.path.join(self.raw_dir, row['local_path'])
            
            if not os.path.exists(pdf_path):
                print(f"⚠️ Warning: File not found: {pdf_path}")
                continue

            print(f"⚙️ Processing: {row['title']}")
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            # Split the document into semantic chunks
            chunks = self.splitter.split_text(raw_text)
            
            for chunk in chunks:
                # FIXED: Metadata must be a simple dictionary passed to Document
                metadata = {
                    "source": row['title'], 
                    "title": row['title'],
                    "url": row['url'],      # Required for the RBI website link
                    "date": row['date']     # Required for accurate citations
                }
                
                # FIXED: Correct variable 'chunk' and simplified constructor
                doc = Document(page_content=chunk, metadata=metadata)
                all_chunks.append(doc)
        
        return all_chunks

if __name__ == "__main__":
    processor = RBIProcessor()
    docs = processor.process_all_documents()
    print(f"✅ Created {len(docs)} semantic chunks with full metadata.")