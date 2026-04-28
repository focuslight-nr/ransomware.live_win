"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os,datetime,sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender,extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")



def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('mnt6-'):
                html_doc = tmp_dir / filename
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    # Extract title
                    title_tag = card.find('h2', class_='card-title')
                    if not title_tag:
                        continue
                    victim = title_tag.get_text(strip=True)
                    
                    # Extract description
                    desc_tag = card.find('p', class_='card-description')
                    description = desc_tag.get_text(strip=True) if desc_tag else ""
                    
                    # Extract link from onclick="location.href='/post/7/'"
                    onclick = card.get('onclick', '')
                    post_url = ""
                    match = re.search(r"location\.href='(.*?)'", onclick)
                    if match:
                        post_url = match.group(1)
                    
                    # Construct full URL using find_slug_by_md5
                    base_url = find_slug_by_md5('mnt6', extract_md5_from_filename(filename))
                    if base_url and post_url.startswith('/'):
                        post_url = base_url.rstrip('/') + post_url
                    
                    appender(
                        victim=victim,
                        group_name='mnt6',
                        description=description,
                        website="",
                        published="",  # appender will use current date
                        post_url=post_url,
                        country=""
                    )
        except Exception as e:
            errlog('mnt6 - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
