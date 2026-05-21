"""
    Parser for Triple X -> appender()
    Signature: def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog
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

def parse_date(date_str):
    # e.g., "11 May 2026"
    date_str = date_str.strip()
    for fmt in ('%d %B %Y', '%d %b %Y'):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            continue
    return ""

def main():
    group_name = "triple x"
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('triplex-'):
                html_doc = tmp_dir / filename
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')
                    
                    try:
                        base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc)))
                    except Exception:
                        base_url = ""
                    
                    posts = soup.find_all('div', class_='post')
                    for post in posts:
                        title_tag = post.find(class_='post-title')
                        if not title_tag:
                            continue
                        title = title_tag.text.strip()
                        
                        date_tag = post.find(class_='post-date')
                        published = parse_date(date_tag.text) if date_tag else ""
                        
                        content_tag = post.find(class_='post-content')
                        description = content_tag.text.strip() if content_tag else ""
                        
                        # Use base_url as post_url since there is no individual link
                        post_url = base_url
                        
                        appender(title, group_name, description=description, published=published, post_url=post_url)
                        
        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
