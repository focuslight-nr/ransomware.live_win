"""
    Parser for CyphBit / CiphBit
    Handles both names as they share the same infrastructure.
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

# Base URL shared by both entries
base_url = "http://ciphbitqyg26jor7eeo6xieyq7reouctefrompp6ogvhqjba7uo4xdid.onion"

def main():
    for filename in os.listdir(tmp_dir):
        # Determine group name from prefix
        current_group = None
        if filename.startswith('cyphbit-'):
            current_group = 'cyphbit'
        elif filename.startswith('ciphbit-'):
            current_group = 'ciphbit'
            
        if current_group:
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {current_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Use the 'card' structure identified for this group
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    try:
                        title_tag = card.find('h2', class_='post-title')
                        if not title_tag:
                            continue
                        victim = title_tag.text.strip()
                        
                        if victim.lower() in ["become affiliate", "become an affiliate"]:
                            continue

                        desc_tag = card.find('div', class_='post-body')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        date_tag = card.find('div', class_='post-meta')
                        published_str = date_tag.text.strip() if date_tag else ""
                        published = ""
                        if published_str:
                             try:
                                 # Trim any leading/trailing space or characters
                                 clean_date = published_str.strip()
                                 published = datetime.strptime(clean_date, "%b %d, %Y").strftime("%Y-%m-%d %H:%M:%S.%f")
                             except Exception as dt_err:
                                 # Fallback for different formats or extra text
                                 pass

                        link_tag = title_tag.find('a', href=True)
                        post_url = urljoin(base_url, link_tag['href']) if link_tag else ""
                        
                        website = ""
                        # If post_url is external, use it as website
                        if post_url and not post_url.startswith('http://') and not post_url.startswith('https://'):
                             pass # Relative or onion

                        appender(victim, current_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{current_group} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{current_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

