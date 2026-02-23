"""
    Parser for Obscura
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))

def main():
    # Covers both 'obscura' and 'obscura 2.0' file naming
    group_patterns = ['obscura-', 'obscura 2.0-']
    
    for filename in os.listdir(tmp_dir):
        matched = False
        for pattern in group_patterns:
            if filename.startswith(pattern):
                matched = True
                break
        
        if matched:
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    try:
                        header = card.find('div', class_='card-header')
                        if not header: continue
                        
                        victim = header.find('span', class_='title').text.strip()
                        website = header.find('span', class_='domain').text.strip()
                        published = header.find('span', class_='created').text.strip()
                        
                        desc_tag = card.find('div', class_='card-desc')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        # Post URL (if available, e.g. from Filelist button)
                        link_tag = card.find('a', class_='filelist-btn', href=True)
                        post_url = link_tag['href'] if link_tag else ""
                        
                        appender(victim, 'obscura', description, website, published, post_url)
                    except Exception as e:
                        errlog(f'obscura - error parsing card: {e}')
            except Exception as e:
                errlog(f'obscura - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
