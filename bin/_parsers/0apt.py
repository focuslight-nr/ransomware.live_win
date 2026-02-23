"""
    Parser for 0APT (Independent Organization)
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

target_group_name = "0apt"
base_url = "http://oaptxiyisljt2kv3we2we34kuudmqda7f2geffoylzpeo7ourhtz4dad.onion"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('0apt-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Using general card structure (to be verified upon first scrape)
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    try:
                        title_tag = card.find(['h3', 'h2'])
                        if not title_tag:
                            continue
                        victim = title_tag.text.strip()
                        
                        desc_tag = card.find('p')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        link_tag = card.find('a', href=True)
                        post_url = urljoin(base_url, link_tag['href']) if link_tag else ""
                        
                        appender(victim, target_group_name, description, "", "", post_url)
                    except Exception as e:
                        errlog(f'{target_group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
