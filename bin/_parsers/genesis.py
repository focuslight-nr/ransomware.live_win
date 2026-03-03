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
    group_name = "genesis"
    stdlog(f"Processing group: {group_name}")
    
    # Base URL for Genesis (can be fetched from metadata if needed)
    base_url = "http://genesis6ixpb5mcy4kudybtw5op2wqlrkocfogbnenz3c647ibqixiad.onion"

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # The items are in <section class="block-bg ...">
                sections = soup.find_all('section', class_=re.compile(r'block-bg'))
                for section in sections:
                    try:
                        # Title is in <h2>
                        title_tag = section.find('h2')
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                        # Description is in div.not-prose
                        description = ""
                        desc_tag = section.find('div', class_='not-prose')
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)

                        # Date is in <time>
                        published = ""
                        time_tag = section.find('time')
                        if time_tag:
                            published = time_tag.get_text(strip=True)

                        # Link is in <a> with class absolute inset-0
                        link = ""
                        link_tag = section.find('a', href=True)
                        if link_tag:
                            link = urljoin(base_url, link_tag['href'])

                        appender(title, group_name, description, '', published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
