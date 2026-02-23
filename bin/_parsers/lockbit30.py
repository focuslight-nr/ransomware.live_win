"""
    Parser for LockBit 3.0
"""

import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('lockbit 3.0-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # LockBit 3.0 uses post-block class for victims
                post_blocks = soup.find_all('a', class_=lambda x: x and 'post-block' in x)
                for block in post_blocks:
                    try:
                        title_div = block.find('div', class_='post-title')
                        if not title_div:
                            continue
                        victim = title_div.text.strip()
                        
                        desc_div = block.find('div', class_='post-block-text')
                        description = desc_div.text.strip() if desc_div else ""
                        
                        published_div = block.find('div', class_='updated-post-date')
                        published = ""
                        if published_div:
                            pub_text = published_div.text.strip().replace('Updated: ', '')
                            try:
                                # Example: "16 Feb, 2026, 10:22 UTC"
                                date_obj = datetime.strptime(pub_text, "%d %b, %Y, %H:%M %Z")
                                published = date_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass
                        
                        link = block.get('href', "")
                        # Base URL from groups.json
                        url = find_slug_by_md5('lockbit3', extract_md5_from_filename(filename))
                        if not url:
                             url = 'http://lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion'
                        else:
                             url = url.rstrip('/')
                        post_url = urljoin(url + '/', link) if link else ""
                        
                        appender(victim, 'lockbit3', description, "", published, post_url)
                    except Exception as e:
                        errlog(f'lockbit3.0 - error parsing card: {e}')
            except Exception as e:
                errlog(f'lockbit3.0 - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
