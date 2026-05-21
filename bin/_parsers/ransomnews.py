"""
    Parser for ransomnews group (threat intelligence / news feed)
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |     X     |     X    |
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
    group_name = 'ransomnews'

    for filename in os.listdir(tmp_dir):
        if not filename.startswith('ransomnews-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find all latest-post cards
            posts = soup.find_all('div', class_='latest-post')
            for post in posts:
                title_h4 = post.find('h4', class_='post-title')
                if not title_h4:
                    continue
                title_a = title_h4.find('a')
                if not title_a:
                    continue

                victim = title_a.text.strip()
                # Clean up any newlines or HTML breaks inside title
                victim = re.sub(r'\s+', ' ', victim).strip()
                
                href = title_a.get('href', '')

                # Description
                text_div = post.find('div', class_='post-text')
                description = text_div.text.strip() if text_div else ""
                description = re.sub(r'\s+', ' ', description).strip()

                # Date
                date_div = post.find('div', class_='post-date')
                pubdate = ""
                if date_div:
                    spans = date_div.find_all('span')
                    if len(spans) >= 2:
                        day_month = spans[0].text.strip()
                        year = spans[1].text.strip()
                        date_str = f"{day_month}.{year}"
                        try:
                            dt = datetime.strptime(date_str, "%d.%m.%Y")
                            pubdate = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                        except Exception:
                            try:
                                dt = datetime.strptime(date_str, "%m.%d.%Y")
                                pubdate = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except Exception:
                                pubdate = ""

                # Resolve post_url
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(filename)) or ""
                # Strip leading/trailing slashes
                base_url = base_url.rstrip('/')
                href = href.lstrip('/')
                post_url = f"{base_url}/{href}"

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website="",
                    published=pubdate,
                    post_url=post_url
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
