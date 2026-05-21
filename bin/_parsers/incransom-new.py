"""
    Parser for inc ransom - new group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |             |    X    |           |     X    |
    +-----------------------+-----------+----------+
"""

import os
import re
from bs4 import BeautifulSoup
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
    group_name = "inc ransom - new"
    prefix = "incransom-new"

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(prefix + '-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find all announcement containers
            announcements = soup.find_all('a', class_='announcement__container')
            for a in announcements:
                name_span = a.find('span', class_=lambda c: c and 'text-white' in c)
                if not name_span:
                    continue

                victim = name_span.text.strip()
                if not victim:
                    continue

                relative_link = a.get('href', '')

                # Normalize victim name if it's a raw URL
                website = ""
                url_match = re.match(r'^https?://([^/]+)/?$', victim)
                if url_match:
                    website = url_match.group(1)
                    victim = website
                elif re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', victim):
                    website = victim

                # Resolve post_url
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(filename)) or ""
                post_url = base_url + relative_link

                appender(
                    victim=victim,
                    group_name=group_name,
                    description="",
                    website=website,
                    published="",
                    post_url=post_url
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
