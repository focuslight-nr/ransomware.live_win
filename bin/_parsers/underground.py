"""
    Parser for Team Underground
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
    group_name = 'underground'
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith('team underground-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Underground store uses a specific grid structure for data
                # We need to find the victim entries
                items = soup.find_all('div', class_='col-md-4') # Based on typical Bootstrap grid
                if not items:
                    # Alternative selector if grid is different
                    items = soup.find_all('div', class_='card')
                
                for item in items:
                    try:
                        title_tag = item.find(['h4', 'h5', 'h3'])
                        if not title_tag: continue
                        victim = title_tag.text.strip()
                        
                        desc_tag = item.find('div', class_='card-body')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        link_tag = item.find('a', href=True)
                        post_url = ""
                        if link_tag:
                            post_url = link_tag['href']
                            if not post_url.startswith('http'):
                                post_url = 'http://underground...onion/' + post_url.lstrip('/')
                        
                        appender(victim, group_name, description, "", "", post_url)
                    except Exception as e:
                        errlog(f'underground - error parsing card: {e}')
            except Exception as e:
                errlog(f'underground - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
