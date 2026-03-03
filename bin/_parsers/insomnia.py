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
    group_name = "insomnia"
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

                # Items are in book-cards
                cards = soup.find_all('div', class_='book-card')
                
                for card in cards:
                    try:
                        # Info section
                        info = card.find('div', class_='card-info')
                        if not info:
                            continue
                        
                        title_tag = info.find('h3', class_='info-title')
                        if not title_tag or not title_tag.find('a'):
                            continue
                        
                        a_tag = title_tag.find('a')
                        title = a_tag.get_text(strip=True)
                        link = urljoin(base_url, a_tag['href']) if base_url else ""

                        industry = ""
                        industry_tag = info.find('p', class_='info-author')
                        if industry_tag:
                            industry = industry_tag.get_text(strip=True)

                        desc = ""
                        desc_tag = info.find('p', class_='info-desc')
                        if desc_tag:
                            desc = desc_tag.get_text(strip=True)

                        # Meta section
                        meta = card.find('div', class_='card-meta')
                        website = ""
                        revenue = ""
                        location = ""
                        published = ""

                        if meta:
                            spans = meta.find_all('span')
                            for span in spans:
                                text = span.get_text(strip=True)
                                if 'Website:' in text:
                                    website = text.replace('Website:', '').strip()
                                elif 'Revenue:' in text:
                                    revenue = text.replace('Revenue:', '').strip()
                                elif 'Location:' in text:
                                    location = text.replace('Location:', '').strip()
                                elif 'Notified:' in text:
                                    date_str = text.replace('Notified:', '').strip()
                                    try:
                                        # Format: 2026-2-14
                                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                                        published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                    except:
                                        published = date_str

                        # Description compilation
                        desc_parts = []
                        if industry: desc_parts.append(f"Industry: {industry}")
                        if revenue: desc_parts.append(f"Revenue: {revenue}")
                        if location: desc_parts.append(f"Location: {location}")
                        if desc: desc_parts.append(desc)
                        full_description = " | ".join(desc_parts)

                        appender(title, group_name, full_description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
