"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os,datetime,sys
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender,extract_md5_from_filename, errlog
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
            if filename.startswith('cmdorganization-'):
                html_doc = tmp_dir / filename
                file = open(html_doc, "r", encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(file, 'html.parser')
                
                # Base URL for post_url
                base_slug = find_slug_by_md5('cmdorganization', extract_md5_from_filename(filename))
                
                # Process Auctions
                auctions = soup.select('.auction-card')
                for auction in auctions:
                    title_element = auction.find('h2')
                    if not title_element:
                        continue
                    
                    link_element = title_element.find('a')
                    victim = link_element.get_text(strip=True) if link_element else title_element.get_text(strip=True)
                    website = link_element['href'] if link_element and 'http' in link_element['href'] else ""
                    
                    description_element = auction.find('div', class_='auction-description')
                    description = description_element.get_text(strip=True) if description_element else ""
                    
                    # Try to get published date from data-end-date or just use now
                    published = ""
                    if auction.has_attr('data-end-date'):
                        try:
                            # 2026-05-08T11:43:41.103137Z
                            date_str = auction['data-end-date'].split('.')[0].rstrip('Z')
                            published = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            pass
                    
                    post_url = base_slug if base_slug else ""
                    
                    appender(victim, 'cmdorganization', description, website, published, post_url)
                
                # Process Latest Companies
                companies = soup.select('.item-card')
                for company in companies:
                    title_element = company.find('h2')
                    if not title_element:
                        continue
                    
                    link_element = title_element.find('a')
                    victim = link_element.get_text(strip=True) if link_element else title_element.get_text(strip=True)
                    website = link_element['href'] if link_element and 'http' in link_element['href'] else ""
                    
                    desc_before = company.find('div', class_='description-before')
                    desc_after = company.find('div', class_='description-after')
                    
                    description = ""
                    if desc_before:
                        description += desc_before.get_text(strip=True)
                    if desc_after:
                        if description: description += " "
                        description += desc_after.get_text(strip=True)
                    
                    post_url = base_slug if base_slug else ""
                    
                    appender(victim, 'cmdorganization', description, website, "", post_url)
                
                file.close()
        except Exception as e:
            errlog('cmdorganization - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
