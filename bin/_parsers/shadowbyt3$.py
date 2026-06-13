"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |             |         |     X     |          |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")



def main():
    date_format = "%Y-%m-%d %H:%M:%S.%f"

    ## Get the ransomware group name from the script name
    script_path = os.path.abspath(__file__)
    # If it's a symbolic link find the link source
    if os.path.islink(script_path):
        original_path = os.readlink(script_path)
        if not os.path.isabs(original_path):
            original_path = os.path.join(os.path.dirname(script_path), original_path)
        original_path = os.path.abspath(original_path)
        original_name = os.path.basename(original_path)
        group_name = original_name.replace('.py', '')
    # else get the script name
    else:
        script_name = os.path.basename(script_path)
        group_name = script_name.replace('.py', '')

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                file = open(html_doc, "r", encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(file, 'html.parser')
                file.close()

                base_url = find_slug_by_md5(
                    group_name,
                    extract_md5_from_filename(str(html_doc)),
                ) or ""
                post_url = urljoin(base_url.rstrip('/') + '/', 'leaks') if base_url else ""

                cards = soup.select('.leak-card')
                if cards:
                    for card in cards:
                        title_element = card.find('h3')
                        if not title_element:
                            continue

                        title = title_element.get_text(" ", strip=True)
                        phrase = card.select_one('.phrase')
                        description = phrase.get_text("\n", strip=True) if phrase else ""
                        if "not a leak just an announcement" in description.lower():
                            continue

                        website = ""
                        website_match = re.search(
                            r"Company Site:\s*(?:https?://)?([^\s/]+)",
                            description,
                            flags=re.IGNORECASE,
                        )
                        if website_match:
                            website = website_match.group(1).strip().rstrip('.,)')
                        else:
                            title_domain = re.search(
                                r"\((?:https?://)?([a-z0-9.-]+\.[a-z]{2,})\)?",
                                title,
                                flags=re.IGNORECASE,
                            )
                            if title_domain:
                                website = title_domain.group(1).lower()

                        size_match = re.search(
                            r"\bsize:\s*([0-9.,]+\s*(?:KB|MB|GB|TB))",
                            description,
                            flags=re.IGNORECASE,
                        )
                        extra_infos = {}
                        if size_match:
                            extra_infos["data_size"] = size_match.group(1).replace(" ", "")

                        appender(
                            title,
                            group_name,
                            description=description,
                            website=website,
                            post_url=post_url,
                            extra_infos=extra_infos,
                        )
                    continue

                # Only process the leaks page (contains the PUBLIC LEAKS header)
                if not soup.find('h1', string=lambda t: t and 'PUBLIC LEAKS' in t):
                    continue

                # Find the leaks table rows (skip header row)
                rows = soup.select('table tbody tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    name = cells[0].get_text(strip=True)
                    release_str = cells[3].get_text(strip=True)

                    # Parse release date
                    published = ''
                    try:
                        date_obj = datetime.strptime(release_str, '%Y-%m-%d %H:%M:%S')
                        published = date_obj.strftime(date_format)
                    except Exception:
                        published = ''

                    if name:
                        appender(name.replace('_LEAK.7z',''), group_name, description='File: '+name, website='', published=published, post_url='', country='')

        except Exception as e:
            errlog(group_name + ' - parsing fail with error: ' + str(e) + ' in file: ' + filename)
