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

class RBIScraper:
    def __init__(self):
        self.url = "https://rbi.org.in/scripts/bs_viewmasterdirections.aspx"
        self.download_path = "/app/data/raw_pdfs"
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
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Finding the specific data table
            table = soup.find('table', {'class': 'table-g-v'})
            if not table:
                # Fallback to largest table if class name changed
                tables = soup.find_all('table')
                table = max(tables, key=lambda x: len(x.find_all('tr')))

            rows = table.find_all('tr')
            metadata = []
            
            # The RBI table structure often uses rows with 'tableheader' class for dates
            # or simply the first column. We'll track the last seen date.
            current_date = "Unknown"

            for row in rows:
                # Check if this row defines a date (common in RBI master direction tables)
                header = row.find('td', class_='tableheader')
                if header and not any(char.isdigit() for char in header.text):
                    # This might be a category header, skip or handle as needed
                    continue
                elif header:
                    current_date = header.text.strip()
                    continue

                # Look for PDF links in standard rows
                anchor = row.find('a', href=lambda x: x and 'PDFs' in x and x.endswith('.pdf'))
                if anchor:
                    link = anchor['href']
                    title_cell = row.find('a', class_='link2')
                    
                    if title_cell:
                        title = title_cell.text.strip()
                        filename = "".join([c if c.isalnum() else "_" for c in title])[:100] + ".pdf"
                        
                        print(f"Downloading: {title} (Date: {current_date})")
                        self.download_file(link, filename)
                        
                        metadata.append({
                            "date": current_date,
                            "title": title,
                            "url": link,
                            "local_path": filename
                        })

            df = pd.DataFrame(metadata)
            df.to_csv("/app/data/metadata.csv", index=False)
            print(f"Successfully scraped {len(metadata)} items with dates.")

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