"""
    Parser for handala redwanted group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
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
    group_name = "handala redwanted"
    prefix = "handalaredwanted"

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(prefix + '-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find all panels
            panels = soup.find_all('section', class_='panel')
            for panel in panels:
                title_a = panel.find('a', class_='pro-title')
                if not title_a:
                    continue

                victim = title_a.text.strip()
                
                # Company/unit
                company_p = panel.find('p', class_='company')
                company = company_p.text.strip() if company_p else ""

                # Find modal and its body
                modal_div = panel.find('div', class_='modal')
                modal_body = modal_div.find('div', class_='modal-body') if modal_div else None
                desc = modal_body.text.strip() if modal_body else ""
                
                if company:
                    if desc:
                        description = f"{company} | {desc}"
                    else:
                        description = company
                else:
                    description = desc

                # Resolve post_url
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(filename)) or ""

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website="",
                    published="",
                    post_url=base_url
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
