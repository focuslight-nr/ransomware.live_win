"""
    Parser for Meduza Locker
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
    # The group name in the files might be 'meduza locker'
    group_name = 'meduza locker'
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Meduza Locker uses article tags with company-card class
                cards = soup.find_all('article', class_='company-card')
                for card in cards:
                    try:
                        title_tag = card.find('h3')
                        if not title_tag: continue
                        victim = title_tag.text.strip()
                        
                        desc_tag = card.find('div', class_='company-card__desc')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        # Date is often in a div with pub-date class
                        date_tag = card.find('div', class_='pub-date')
                        published = ""
                        if date_tag and date_tag.text.strip() != "—":
                            published = date_tag.text.strip()
                        
                        # Post URL
                        link_tag = card.find('a', class_='company-card__more', href=True)
                        post_url = ""
                        if link_tag:
                            post_url = 'http://meduza...onion' + link_tag['href'] # Base URL placeholder
                        
                        appender(victim, group_name, description, "", published, post_url)
                    except Exception as e:
                        errlog(f'{group_name} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
