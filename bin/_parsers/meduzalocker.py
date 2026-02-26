"""
    Parser for Meduza Locker
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
import re

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "meduzalocker"
    for filename in os.listdir(tmp_dir):
        if filename.startswith("meduza locker-"):
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

                articles = soup.find_all('article', class_='company-card')
                for article in articles:
                    try:
                        title_tag = article.find('h3')
                        if not title_tag:
                            continue
                        victim = title_tag.get_text(strip=True)

                        # website often matches victim name if it looks like a domain
                        website = ""
                        if re.search(r'[a-z0-9-]+\.[a-z]{2,6}', victim.lower()):
                            website = victim.lower()

                        description = ""
                        desc_div = article.find('div', class_='company-card__desc')
                        if desc_div:
                            description = desc_div.get_text(strip=True)

                        # post_url
                        post_url = ""
                        more_a = article.find('a', class_='company-card__more')
                        if more_a:
                            post_url = urljoin(base_url, more_a['href']) if base_url else more_a['href']

                        # Date is not directly in the card, but might be in meta or missing
                        published = ""
                        
                        appender(victim, target_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing article: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

