"""
    Parser for cry0 group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |     X     |     X    |
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
    group_name = 'cry0'

    for filename in os.listdir(tmp_dir):
        if not filename.startswith('cry0-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find the grid element
            grid = soup.find('div', style=lambda s: s and 'grid-template-columns' in s)
            if not grid:
                continue

            # Every immediate child of the grid is a card
            cards = grid.find_all('div', recursive=False)
            for card in cards:
                h3 = card.find('h3')
                if not h3:
                    continue
                
                victim = h3.text.strip()
                
                # Description
                p = card.find('p', style=lambda s: s and 'color' in s)
                description = p.text.strip() if p else ""
                
                # Date
                date_div = card.find('div', style=lambda s: s and 'border-top' in s)
                date_str = date_div.text.strip() if date_div else ""
                
                pubdate = ""
                if date_str:
                    try:
                        dt = datetime.strptime(date_str, "%m/%d/%Y")
                        pubdate = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                    except Exception:
                        try:
                            dt = datetime.strptime(date_str, "%d/%m/%Y")
                            pubdate = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                        except Exception:
                            pubdate = ""

                # Website
                website = ""
                if re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', victim):
                    website = victim

                link = find_slug_by_md5(group_name, extract_md5_from_filename(filename)) or ""

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website=website,
                    published=pubdate,
                    post_url=link
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
