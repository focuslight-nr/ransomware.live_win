"""
    Parser for Leaknet
"""

import os, json, re
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('leaknet-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Leaknet stores data in a script tag as INIT_DATA
                script = soup.find('script', string=re.compile('globalThis.INIT_DATA'))
                if script:
                    try:
                        # Improved regex to find JSON within backticks
                        match = re.search(r'JSON\.parse\(`(.*?)`\)', script.string, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                            # Handle common escape sequences in JS template literals/JSON.parse
                            # Instead of a simple replace, we use a more robust way to unescape
                            try:
                                # json_str is literally "{\"key\": \"val\"}"
                                # We need to turn it into {"key": "val"}
                                json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                                data = json.loads(json_str)
                                articles = data.get('article_list_response', {}).get('result', {}).get('data', [])
                                for art in articles:
                                    victim = art.get('article_title', 'Unknown')
                                    description = art.get('article_brief', '')
                                    website = art.get('subject_site', '')
                                    # Convert UNIX timestamp to YYYY-MM-DD HH:MM:SS.f
                                    from datetime import datetime
                                    ts = art.get('article_added_timestamp', 0)
                                    published = ""
                                    if ts:
                                        published = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.f')
                                    post_url = ""
                                    appender(victim, 'leaknet', description, website, published, post_url)
                            except Exception as json_err:
                                errlog(f"leaknet - JSON loads failed: {json_err}")
                    except Exception as e:
                        errlog(f"leaknet - script parsing error: {e}")
                        errlog(f'leaknet - error parsing JSON: {e}')
                
                # Fallback: Parse visible cards if script parsing fails
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    title_tag = card.find('h5', class_='card-title')
                    if not title_tag: continue
                    victim = title_tag.text.strip()
                    
                    # Check if already processed via JSON (simple duplicate check for this run)
                    desc_tag = card.find('p', class_='card-text')
                    description = desc_tag.text.strip() if desc_tag else ""
                    
                    link_tag = card.find('a', class_='card-link', href=True)
                    website = link_tag['href'] if link_tag else ""
                    
                    view_link = card.find('a', string=re.compile('VIEW'), href=True)
                    post_url = ""
                    if view_link:
                        post_url = 'http://leaknet...onion/' + view_link['href'].lstrip('/') # Base URL needed
                    
                    appender(victim, 'leaknet', description, website, "", post_url)

            except Exception as e:
                errlog(f'leaknet - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
