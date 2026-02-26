"""
    Parser for Insomnia
    Works with rendered HTML (even if CAPTCHA is present, data is often hidden in HTML)
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
import re
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "insomnia"
    filenames = os.listdir(tmp_dir)
    
    for filename in filenames:
        if filename.startswith(f"{target_group}-") or filename == "insomnia_rendered_test.html":
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                # Cards are in div.book-card
                cards = soup.find_all('div', class_='book-card')
                for card in cards:
                    try:
                        # Title
                        title_tag = card.find('h3', class_='info-title')
                        if not title_tag:
                            continue
                        victim = title_tag.get_text(strip=True)

                        # Description
                        description = ""
                        desc_p = card.find('p', class_='info-desc')
                        if desc_p:
                            description = desc_p.get_text(strip=True)

                        # Website & Date (inside card-meta)
                        website = ""
                        published = ""
                        country = ""
                        meta_div = card.find('div', class_='card-meta')
                        if meta_div:
                            meta_text = meta_div.get_text(separator="|", strip=True)
                            # Website: www.zaner.com
                            ws_match = re.search(r'Website:\|(.*?)(?:\||$)', meta_text)
                            if ws_match:
                                website = ws_match.group(1).strip()
                            
                            # Notified: 2026-2-4
                            date_match = re.search(r'Notified:\|(.*?)(?:\||$)', meta_text)
                            if date_match:
                                date_str = date_match.group(1).strip()
                                try:
                                    # Handle "YYYY-M-D"
                                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = date_str
                            
                            # Location: Chicago, Illinois, USA
                            loc_match = re.search(r'Location:\|(.*?)(?:\||$)', meta_text)
                            if loc_match:
                                country = loc_match.group(1).strip()

                        # post_url
                        post_url = ""
                        link_a = title_tag.find('a', href=True)
                        if link_a:
                            post_url = urljoin(base_url, link_a['href']) if base_url else link_a['href']

                        appender(victim, target_group, description, website, published, post_url, country)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

