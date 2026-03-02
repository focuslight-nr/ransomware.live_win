"""
    Brain Cipher Parser
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, datetime, sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "braincipher"
    stdlog(f"Searching for files starting with '{group_name}-' in {tmp_dir}")

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                
                # The HTML structure for Brain Cipher
                # <article class="news-item">
                #   <h2 class="headline"><a href="...">...</a></h2>
                #   <p class="summary">...</p>
                # </article>
                
                news_items = soup.find_all('article', class_='news-item')
                if news_items:
                    stdlog(f"Found {len(news_items)} news items for {group_name} in {filename}")
                    
                    # Try to get base URL if possible
                    target_md5 = extract_md5_from_filename(filename)
                    base_url = find_slug_by_md5(group_name, target_md5)
                    if base_url:
                        base_url = base_url.rstrip('/')
                    else:
                        base_url = ""

                    for item in news_items:
                        try:
                            headline_tag = item.find('h2', class_='headline')
                            if headline_tag:
                                link_tag = headline_tag.find('a')
                                if link_tag:
                                    title = link_tag.text.strip()
                                    link = link_tag.get('href', '')
                                    if link.startswith('/') and base_url:
                                        full_link = base_url + link
                                    else:
                                        full_link = link
                                else:
                                    title = headline_tag.text.strip()
                                    full_link = ""
                            else:
                                continue # Skip if no headline

                            description_tag = item.find('p', class_='summary')
                            description = description_tag.text.strip() if description_tag else ""

                            # Check for labels (PENDING / RELEASED)
                            label_tag = item.find('span', class_='label')
                            if label_tag:
                                label = label_tag.text.strip()
                                # Could use label to filter or add to description
                                if label == "PENDING":
                                    description = f"[PENDING] {description}"
                            
                            appender(title, group_name, description, '', '', full_link)
                        except Exception as e:
                            errlog(f"{group_name} - entry parse fail: {e} in file: {filename}")
                else:
                    errlog(f"{group_name} - no items found in file: {filename}")

if __name__ == "__main__":
    main()
