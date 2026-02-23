"""
    Parser for Blackout
"""

import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))

def main():
    group_name = 'blackout'
    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Blackout cards
                cards = soup.find_all('div', class_=lambda x: x and 'card' in x)
                for card in cards:
                    try:
                        link_tag = card.find('a', href=re.compile(r'/post/'))
                        if not link_tag:
                            continue
                            
                        victim = link_tag.text.strip()
                        
                        # Sometimes the title is in a p tag with card-title class
                        title_p = card.find('p', class_=re.compile(r'card-title', re.I))
                        if title_p and not victim:
                            victim = title_p.text.strip()
                        
                        if not victim:
                            continue

                        post_url = link_tag['href']
                        if not post_url.startswith('http'):
                            # Base URL for blackout
                            base_url = 'http://blackout274a61f779ca1132044f7dea5ddae395.onion'
                            post_url = urljoin(base_url, post_url)
                        
                        desc_p = card.find('p', class_='card-text')
                        description = desc_p.text.strip() if desc_p else ""
                        
                        appender(victim, group_name, description, "", "", post_url)
                    except Exception as e:
                        errlog(f'{group_name} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
