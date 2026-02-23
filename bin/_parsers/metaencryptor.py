"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os,datetime,sys,re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender,extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME")
tmp_dir = Path(home + os.getenv("TMP_DIR"))


from urllib.parse import urljoin

def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('metaencryptor-') or filename.startswith('metaencrypter-'):
                html_doc= tmp_dir / filename
                file=open(html_doc, 'r', encoding='utf-8')
                soup=BeautifulSoup(file,'html.parser')
                # Find all victim cards
                cards = soup.find_all('div', class_='col d-flex align-items-stretch mb-3')
                for card in cards:
                    header = card.find('div', class_='card-header')
                    if not header: continue
                    victim = header.get_text(strip=True)
                    
                    desc_tag = card.find('p', class_='card-text')
                    description = desc_tag.get_text(strip=True) if desc_tag else ""
                    
                    website_link = card.find('a', class_='btn btn-secondary btn-sm', href=True)
                    website = website_link['href'] if website_link and not website_link['href'].startswith('#') else ""
                    
                    post_link = card.find('a', class_='btn btn-primary btn-sm', href=True)
                    post_url = ""
                    if post_link:
                        base_url = find_slug_by_md5('metaencryptor', extract_md5_from_filename(filename))
                        if not base_url:
                            base_url = "http://metacrptmytukkj7ajwjovdpjqzd7esg5v3sg344uzhigagpezcqlpyd.onion"
                        post_url = urljoin(base_url.rstrip('/') + '/', post_link['href'].lstrip('/'))
                    
                    appender(victim, 'metaencryptor', description, website, '', post_url)
                file.close()
        except Exception as e:
            errlog('metaencryptor - parsing fail with error: ' + str(e))
