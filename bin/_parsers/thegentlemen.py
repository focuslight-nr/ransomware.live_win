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
    group_name = "the gentlemen"
    # For matching filename which is usually normalized
    file_prefix = "thegentlemen"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(file_prefix + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL for links
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                # Items are in cards
                cards = soup.find_all('div', class_='card')
                
                for card in cards:
                    try:
                        # Title
                        title_tag = card.find('div', class_='card-title')
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                        # Description
                        description = ""
                        desc_tag = card.find('div', class_='card-desc')
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)

                        # Extract website from description
                        website = ""
                        if description:
                            # Look for strings ending in .com, .net, etc. at the start
                            match = re.search(r'^([a-z0-9.-]+\.[a-z]{2,})', description.lower())
                            if match:
                                website = match.group(1)

                        # Status from buttons
                        published = ""
                        btn = card.find('button', class_='card-btn')
                        if btn:
                            status_text = btn.get_text(strip=True)
                            if "Activates in" in status_text:
                                published = status_text # Still counting down
                            else:
                                published = "Published"

                        # Link
                        link = base_url

                        appender(title, group_name, description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
