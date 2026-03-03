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
    group_name = "obscura2.0"
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

                # Items are in cards
                cards = soup.find_all('div', class_='card')
                
                for card in cards:
                    try:
                        header = card.find('div', class_='card-header')
                        if not header:
                            continue
                        
                        title_tag = header.find('span', class_='title')
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                        domain_tag = header.find('span', class_='domain')
                        website = domain_tag.get_text(strip=True) if domain_tag else ""

                        industry_tag = header.find('span', class_='industry')
                        industry = industry_tag.get_text(strip=True) if industry_tag else ""

                        size_tag = header.find('span', class_='size')
                        size = size_tag.get_text(strip=True) if size_tag else ""

                        status_tag = header.find('span', class_='status')
                        status = status_tag.get_text(strip=True) if status_tag else ""

                        date_tag = header.find('span', class_='created')
                        published = ""
                        if date_tag:
                            date_str = date_tag.get_text(strip=True)
                            try:
                                # Format: 2026-01-11 09:32
                                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        description = ""
                        desc_tag = card.find('div', class_='card-desc')
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)

                        desc_parts = []
                        if description: desc_parts.append(description)
                        if industry: desc_parts.append(f"Industry: {industry}")
                        if size: desc_parts.append(f"Size: {size}")
                        if status: desc_parts.append(f"Status: {status}")
                        full_description = " | ".join(desc_parts)

                        link = ""
                        footer = card.find('div', class_='card-footer')
                        if footer:
                            a_tag = footer.find('a', class_='filelist-btn')
                            if a_tag:
                                link = a_tag['href']
                        
                        if not link:
                            link = base_url

                        appender(title, group_name, full_description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
