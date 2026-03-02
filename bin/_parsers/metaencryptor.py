import os, datetime, sys, re
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
    group_name = "metaencryptor"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('metaencryptor-') or filename.startswith('metaencrypter-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Find all victim cards
                cards = soup.find_all('div', class_='col d-flex align-items-stretch mb-3')
                if not cards:
                    # Alternative selector
                    cards = soup.find_all('div', class_='card')

                for card in cards:
                    header = card.find('div', class_='card-header')
                    if not header: continue
                    victim = header.get_text(strip=True)
                    
                    desc_tag = card.find('p', class_='card-text')
                    description = desc_tag.get_text(strip=True) if desc_tag else ""
                    
                    website_link = card.find('a', class_='btn btn-secondary btn-sm', href=True)
                    website = website_link['href'] if website_link and not website_link['href'].startswith('#') else ""
                    
                    post_link = card.find('a', class_='btn btn-primary btn-sm', href=True)
                    post_url = ""
                    if post_link:
                        base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc)))
                        if not base_url:
                            base_url = "http://metacrptmytukkj7ajwjovdpjqzd7esg5v3sg344uzhigagpezcqlpyd.onion"
                        post_url = urljoin(base_url.rstrip('/') + '/', post_link['href'].lstrip('/'))
                    
                    appender(victim, group_name, description, website, '', post_url)
        except Exception as e:
            errlog(f'{group_name} - parsing fail with error: {e}')

if __name__ == "__main__":
    main()
