"""
    Parser for Morpheus (HTML Version)
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
import re
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "morpheus"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f"{target_group}-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                # Posts are in div.post
                posts = soup.find_all('div', class_='post')
                for post in posts:
                    try:
                        # Victim name is in post__header__title
                        victim_tag = post.find('div', class_='post__header__title')
                        victim = victim_tag.get_text(strip=True) if victim_tag else ""
                        
                        if not victim or "New publication" in victim:
                            # Skip placeholder or header-only entries
                            continue

                        # Description and Website are in post__text
                        content_div = post.find('div', class_='post__text')
                        description = content_div.get_text(strip=True) if content_div else ""
                        
                        website = ""
                        if content_div:
                            # Try to find a link or a "Website:" pattern
                            website_match = re.search(r'Website:\s*([a-zA-Z0-9.-]+\.[a-z]{2,6})', content_div.get_text())
                            if website_match:
                                website = website_match.group(1).lower()

                        # Date is in span.formatted-date
                        published = ""
                        date_tag = post.find('span', class_='formatted-date')
                        if date_tag:
                            date_str = date_tag.get_text(strip=True)
                            # Format: "2026-01-29 21:07"
                            try:
                                # Just take the date part or parse full
                                clean_date = date_str.split(' ')[0] 
                                dt = datetime.strptime(clean_date, "%Y-%m-%d")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        post_url = ""
                        link_a = post.find('a', href=re.compile(r'/files/'))
                        if link_a and base_url:
                            post_url = urljoin(base_url, link_a['href'])

                        if victim:
                            appender(victim, target_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing post: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

