"""
    Parser for Orion
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))

def main():
    group_name = 'orion'
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                cards = soup.find_all('div', class_='post-card')
                for card in cards:
                    try:
                        title_tag = card.find('h5', class_='card-title')
                        if not title_tag: continue
                        victim = title_tag.text.strip()
                        
                        # Company name might be different from post title
                        company_tag = card.find('span', class_='company-name')
                        if company_tag and company_tag.text.strip().lower() != victim.lower():
                            victim = f"{victim} ({company_tag.text.strip()})"
                        
                        date_tag = card.find('small', class_='leak-date')
                        published = ""
                        if date_tag:
                            pub_text = date_tag.text.strip()
                            try:
                                # Example: "Jan 26, 2026"
                                date_obj = datetime.strptime(pub_text, "%b %d, %Y")
                                published = date_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = pub_text
                        
                        desc_tag = card.find('p', class_='card-text')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        # Post URL
                        link_tag = card.find('a', class_='btn-outline-danger', href=True)
                        post_url = ""
                        if link_tag:
                            post_url = link_tag['href']
                            if not post_url.startswith('http'):
                                post_url = 'http://orion...onion/' + post_url.lstrip('./')
                        
                        appender(victim, group_name, description, "", published, post_url)
                    except Exception as e:
                        errlog(f'orion - error parsing card: {e}')
            except Exception as e:
                errlog(f'orion - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
