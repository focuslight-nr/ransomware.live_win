"""
    Parser for Malas
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
    for filename in os.listdir(tmp_dir):
        if filename.startswith('malas-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Malas lists victims under "Latest Posts"
                # Pattern: <p> <time>... <a href="...">Victim Name</a> </p>
                posts = soup.find_all('p')
                for p in posts:
                    time_tag = p.find('time')
                    link_tag = p.find('a', href=True)
                    
                    if time_tag and link_tag:
                        victim = link_tag.text.strip()
                        post_url = link_tag['href']
                        pub_date = time_tag.get('datetime', '')
                        
                        # Convert YYYY-MM-DD to standard format
                        try:
                            if pub_date:
                                date_obj = datetime.strptime(pub_date, '%Y-%m-%d')
                                pub_date = date_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            pass
                        
                        appender(victim, 'malas', "", "", pub_date, post_url)

            except Exception as e:
                errlog(f'malas - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
