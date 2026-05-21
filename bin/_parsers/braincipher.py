"""
    Parser for brain cipher group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |           |     X    |
    +-----------------------+-----------+----------+
"""

import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    # Explicitly set the group name as in groups.json
    group_name = "brain cipher"
    prefix = "braincipher"

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(prefix + '-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')

            articles = soup.find_all('article', class_='news-item')
            for art in articles:
                headline_a = art.find('h2', class_='headline')
                if headline_a:
                    headline_a = headline_a.find('a')
                if not headline_a:
                    continue

                victim = headline_a.text.strip()
                relative_link = headline_a.get('href', '')
                
                # Description/summary
                summary_p = art.find('p', class_='summary')
                description = summary_p.text.strip() if summary_p else ""

                # Website
                website = ""
                if re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', victim):
                    website = victim

                # Resolve post_url
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(filename)) or ""
                post_url = base_url + relative_link

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website=website,
                    published="",
                    post_url=post_url
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
