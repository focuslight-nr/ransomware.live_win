"""
    Parser for Reynolds
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
    group_name = 'reynolds'
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Reynolds uses section tags with post-item class
                posts = soup.find_all('section', class_='post-item')
                for post in posts:
                    try:
                        title_tag = post.find('h2', class_='post-title')
                        if not title_tag: continue
                        victim = title_tag.text.strip()
                        
                        desc_tag = post.find('div', class_='post-abstract')
                        description = desc_tag.text.strip() if desc_tag else ""
                        if description.startswith("about"):
                            description = description[5:].strip()
                        
                        date_tag = post.find('div', class_='post-info')
                        published = ""
                        if date_tag:
                            published = date_tag.text.strip()
                        
                        link_tag = post.find('a', href=True)
                        post_url = link_tag['href'] if link_tag else ""
                        
                        appender(victim, group_name, description, "", published, post_url)
                    except Exception as e:
                        errlog(f'{group_name} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
