import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "metaencrypter"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL for links
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                # Current layout cards.
                cards = soup.select('div.lt-card')

                for card in cards:
                    try:
                        title_tag = card.select_one('.lt-card-name')
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                        description = ""
                        desc_tag = card.select_one('.lt-card-memo')
                        if desc_tag:
                            description = desc_tag.get_text(" ", strip=True)

                        meta = {}
                        for row in card.select('.lt-meta-row'):
                            key = row.select_one('.lt-meta-key')
                            val = row.select_one('.lt-meta-val')
                            if key and val:
                                meta[key.get_text(" ", strip=True).lower()] = val.get_text(" ", strip=True)

                        website = ""
                        link = ""
                        site_link = card.select_one('a.lt-btn-site[href]')
                        if site_link:
                            website = site_link['href']

                        browse_link = card.select_one('a.lt-btn-files[href]')
                        if browse_link and base_url:
                            link = urljoin(base_url, browse_link['href'])

                        published = ""
                        extra_infos = {}
                        if meta.get("data size"):
                            extra_infos["data_size"] = meta["data size"]
                        if meta.get("revenue"):
                            extra_infos["revenue"] = meta["revenue"]
                        if meta.get("deadline"):
                            extra_infos["deadline"] = meta["deadline"]

                        appender(title, group_name, description, website, published, link, country=meta.get("country", ""), extra_infos=extra_infos)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
