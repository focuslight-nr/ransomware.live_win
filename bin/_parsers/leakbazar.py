"""
    Leak Bazar Parser
    Extracts victim data from Leak Bazar ransomware group pages.
"""

import os, datetime, sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('leakbazar-') and filename.endswith('.html'):
                html_doc = tmp_dir / filename
                
                # Try to get base URL for full post links
                md5 = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5('leak bazar', md5)
                if not base_url:
                    base_url = ""
                base_url = base_url.rstrip('/')

                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')
                    
                    cards = soup.find_all('div', class_='company-card')
                    for card in cards:
                        name_el = card.find('h3', class_='company-name')
                        if not name_el:
                            continue
                        name = name_el.text.strip()
                        
                        link_el = name_el.find('a')
                        link = link_el.get('href', '') if link_el else ""
                        if link.startswith('/') and base_url:
                            link = base_url + link
                        
                        desc_el = card.find('p', class_='description')
                        description = desc_el.text.strip() if desc_el else ""
                        
                        # Data size
                        size = ""
                        details = card.find_all('div', class_='detail-item')
                        for detail in details:
                            if 'Total Data Size:' in detail.text:
                                size = detail.text.replace('Total Data Size:', '').strip()
                                if size:
                                    description += f"\n\nTotal Data Size: {size}"
                                break
                        
                        # Price
                        price_el = card.find('div', class_='price')
                        if price_el:
                            price = price_el.text.strip()
                            if price:
                                description += f"\n\nPrice: {price}"

                        # Published date from "Updated: YYYY-MM-DD"
                        published = ""
                        updated_el = card.find('div', class_='last-updated')
                        if updated_el:
                            date_match = re.search(r'\d{4}-\d{2}-\d{2}', updated_el.text)
                            if date_match:
                                try:
                                    published = datetime.strptime(date_match.group(), "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    pass
                        
                        appender(
                            victim=name,
                            group_name='leak bazar',
                            description=description,
                            website="",
                            published=published,
                            post_url=link,
                            country=""
                        )
        except Exception as e:
            errlog('leak bazar - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
