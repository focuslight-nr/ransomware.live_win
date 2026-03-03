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
    group_name = "vect"
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

                # Items are in victim-cards
                cards = soup.find_all('div', class_='victim-card')
                
                for card in cards:
                    try:
                        # Title
                        header = card.find('div', class_='card-header-warning')
                        if not header:
                            continue
                        
                        h3 = header.find('h3')
                        if not h3:
                            continue
                        title = h3.get_text(strip=True)

                        # Status
                        status = ""
                        status_tag = header.find('p', class_='status-tag')
                        if status_tag:
                            status = status_tag.get_text(strip=True)

                        # Body section
                        body = card.find('div', class_='card-body')
                        if not body:
                            continue

                        # Date
                        published = ""
                        date_info = body.find('p', class_='date-info')
                        if date_info:
                            date_text = date_info.get_text(strip=True)
                            # Format example: ENTRY 05 | 28 Feb 2026 | DEADLINE...
                            match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', date_text)
                            if match:
                                try:
                                    dt = datetime.strptime(match.group(1), "%d %b %Y")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = match.group(1)

                        # Meta (Sector, Country, Site)
                        website = ""
                        country = ""
                        sector = ""
                        meta_tag = body.find('p', class_='card-meta')
                        if meta_tag:
                            meta_text = meta_tag.get_text(separator=' ', strip=True)
                            if 'SECTOR:' in meta_text:
                                sector = meta_text.split('SECTOR:')[1].split('窶｢')[0].split('COUNTRY:')[0].strip()
                            if 'COUNTRY:' in meta_text:
                                country = meta_text.split('COUNTRY:')[1].split('窶｢')[0].split('SITE:')[0].strip()
                            if 'SITE:' in meta_text:
                                website = meta_text.split('SITE:')[1].strip()

                        # Description and Size
                        desc_parts = []
                        if status: desc_parts.append(f"Status: {status}")
                        if sector: desc_parts.append(f"Sector: {sector}")
                        
                        # Find other p tags that are not date-info or card-meta
                        all_ps = body.find_all('p', recursive=False)
                        for p in all_ps:
                            p_class = p.get('class', [])
                            if 'date-info' not in p_class and 'card-meta' not in p_class:
                                text = p.get_text(strip=True)
                                if text:
                                    desc_parts.append(text)

                        description = " | ".join(desc_parts)

                        link = base_url

                        appender(title, group_name, description, website, published, link, country)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
