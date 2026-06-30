"""
    Parser for Leaknet
"""

import codecs
import json
import os
import re
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
                with open(html_doc, 'r', encoding='utf-8', errors='ignore') as file:
                    html = file.read()
                soup = BeautifulSoup(html, 'html.parser')

                json_items_found = False
                match = re.search(r'JSON\.parse\(`(.*?)`\)', html, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1)
                        json_str = codecs.decode(json_str, 'unicode_escape')
                        json_str = json_str.replace('\\/', '/').replace("\\'", "'")
                        data = json.loads(json_str)
                        articles = data.get('article_list_response', {}).get('result', {}).get('data', [])
                        for art in articles:
                            json_items_found = True
                            victim = art.get('article_title', 'Unknown')
                            description = art.get('article_brief', '')
                            website = re.sub(r'^https?://', '', art.get('subject_site', '')).rstrip('/')
                            from datetime import datetime
                            ts = art.get('article_added_timestamp', 0)
                            published = ""
                            if ts:
                                published = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f')
                            post_url = art.get('author_url', '')
                            appender(victim, 'leaknet', description, website, published, post_url)
                    except Exception as json_err:
                        errlog(f"leaknet - JSON loads failed: {json_err}")

                if json_items_found:
                    continue
                
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
