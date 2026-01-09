# https://rbi.org.in/scripts/bs_viewmasterdirections.aspx
import os
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

class RBIScraper:
    def __init__(self):
        # The URL remains the same
        self.url = "https://rbi.org.in/scripts/bs_viewmasterdirections.aspx"
        self.download_path = "/app/data/raw_pdfs"
        self.metadata_path = "/app/data/metadata.csv"
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def scrape_and_download(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        print(f"Opening {self.url}...")
        
        try:
            driver.get(self.url)
            # Wait longer to ensure the large list of 262+ items is rendered
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))

            # Trigger any 'Expand All' or specific date loads if necessary 
            # (Though you mentioned they are all on one page, this ensures visibility)
            time.sleep(5) 

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # --- GLOBAL DEEP SCAN LOGIC ---
            # We look for all anchor tags that contain 'PDFs' in the link
            all_links = soup.find_all('a', href=lambda x: x and 'PDFs' in x and x.lower().endswith('.pdf'))
            
            metadata = []
            seen_urls = set()
            
            print(f"Discovered {len(all_links)} potential PDF links. Starting deep extraction...")

            for anchor in all_links:
                link = anchor['href']
                
                # De-duplication check
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                # 1. Extraction Logic: Finding the true Title
                # If the link text is just '422 kb' or 'PDF', we look for the preceding text
                title = anchor.get_text(strip=True)
                
                if not title or title.lower().endswith('kb') or len(title) < 10:
                    # Look for the 'link2' class you previously used, or the parent row text
                    parent_row = anchor.find_parent('tr')
                    if parent_row:
                        title_cell = parent_row.find('a', class_='link2')
                        if title_cell:
                            title = title_cell.get_text(strip=True)
                        else:
                            # Fallback: take all text in the row before the 'kb' size mention
                            title = parent_row.get_text(separator=" ", strip=True).split('kb')[0].strip()

                # 2. Extraction Logic: Finding the Date
                # We search upwards for the nearest tableheader or date pattern
                current_date = "Nov 28, 2025" # Default fallback for the 2025 set
                parent_row = anchor.find_parent('tr')
                if parent_row:
                    # Search previous siblings for the date header
                    prev = parent_row.find_previous_sibling('tr')
                    while prev:
                        date_cell = prev.find('td', class_='tableheader')
                        if date_cell and any(char.isdigit() for char in date_cell.text):
                            current_date = date_cell.text.strip()
                            break
                        prev = prev.find_previous_sibling('tr')

                # 3. Save Logic
                # Use same naming convention as before to avoid breaking local_path references
                filename = "".join([c if c.isalnum() else "_" for c in title])[:120] + ".pdf"
                
                print(f"[{len(metadata)+1}] Downloading: {title} (Date: {current_date})")
                self.download_file(link, filename)
                
                # Maintain exact variable names for Indexer compatibility
                metadata.append({
                    "date": current_date,
                    "title": title,
                    "url": link,
                    "local_path": filename
                })

            # Save metadata using exact same path and structure
            df = pd.DataFrame(metadata)
            df.to_csv(self.metadata_path, index=False)
            print(f"\n✅ SUCCESS: Scraped {len(metadata)} items into {self.metadata_path}")

        finally:
            driver.quit()

    def download_file(self, url, filename):
        try:
            r = requests.get(url, stream=True, timeout=30)
            if r.status_code == 200:
                with open(os.path.join(self.download_path, filename), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    scraper = RBIScraper()
    scraper.scrape_and_download()