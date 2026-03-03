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

                # Items are in cards
                cards = soup.find_all('div', class_=re.compile(r'card shadow-sm border-info'))
                
                for card in cards:
                    try:
                        # Title
                        header = card.find('div', class_='card-header')
                        if not header:
                            continue
                        title = header.get_text(strip=True)

                        # Description and Size
                        description = ""
                        body = card.find('div', class_='card-body')
                        if body:
                            desc_tag = body.find('p', class_='card-text')
                            if desc_tag:
                                description = desc_tag.get_text(strip=True)
                            
                            size_tag = body.find('li', string=re.compile(r'Data size'))
                            if size_tag:
                                size_val = size_tag.get_text(strip=True)
                                description = f"[{size_val}] {description}"

                        # Website and Post URL
                        website = ""
                        link = ""
                        footer = card.find('div', class_='card-footer')
                        if footer:
                            # Visit site link
                            visit_link = footer.find('a', string=re.compile(r'Visit site'))
                            if visit_link:
                                website = visit_link['href']
                            
                            # Browse files link
                            browse_link = footer.find('a', string=re.compile(r'Browse files'))
                            if browse_link and base_url:
                                link = urljoin(base_url, browse_link['href'])

                        # Date (relative)
                        published = ""
                        date_tag = footer.find('small', class_='text-muted') if footer else None
                        if date_tag:
                            published = date_tag.get_text(strip=True)

                        appender(title, group_name, description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
