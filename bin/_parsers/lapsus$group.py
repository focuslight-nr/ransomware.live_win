"""
    Parser for lapsus$ group group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |             |         |           |     X    |
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

def clean_title(title):
    title = re.sub(r'\d+GB', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\d+M\s+records', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'\bExtranet\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bInternal\s+Data\b', '', title, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', title).strip()

def main():
    # Explicitly set the group name as in groups.json
    group_name = "lapsus$ group"
    prefix = "lapsus$group"

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(prefix + '-'):
                html_doc = tmp_dir / filename
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')

                items = soup.find_all('div', class_='target-card')
                for item in items:
                    # Skip pending/awaiting upload entries
                    if item.find('span', class_='status-pending'):
                        continue

                    title = clean_title(item.get('data-name', ''))
                    published = item.get('data-date', '')

                    # Extract description from leak-date text after the " | " separator
                    description = ""
                    leak_date_div = item.find('div', class_='leak-date')
                    if leak_date_div:
                        leak_text = leak_date_div.get_text(strip=True)
                        if ' | ' in leak_text:
                            description = leak_text.split(' | ', 1)[1].strip()

                    # First mirror link as post_url
                    post_url = ""
                    first_link = item.find('a', class_='m-link')
                    if first_link:
                        post_url = first_link.get('href', '')

                    appender(
                        victim=title,
                        group_name=group_name,
                        description=description,
                        website="",
                        published=published,
                        post_url=post_url,
                        country=""
                    )
        except Exception as e:
            errlog(group_name + ' - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
