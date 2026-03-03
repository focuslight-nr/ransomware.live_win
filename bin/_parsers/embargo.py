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
    group_name = "embargo"
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

                # Items are in grid columns
                items = soup.find_all('div', class_=re.compile(r'col-12.*xl-4.*p-2'))
                
                for item in items:
                    try:
                        # Title
                        title_tag = item.find('div', class_='blog-title')
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)

                        # Website (often in title)
                        website = ""
                        if '.' in title and ' ' not in title:
                            website = title

                        # Description
                        desc_parts = []
                        preview = item.find('div', class_='blog-preview')
                        if preview:
                            for div in preview.find_all('div', recursive=False):
                                text = div.get_text(strip=True)
                                if text:
                                    desc_parts.append(text)
                        
                        description = " | ".join(desc_parts)

                        # Date
                        published = ""
                        footer_flex = item.find('div', class_='flex justify-content-between')
                        if footer_flex:
                            date_span = footer_flex.find('span')
                            if date_span:
                                date_str = date_span.get_text(strip=True)
                                try:
                                    # Format: 07/12/2025, 02:14:26
                                    dt = datetime.strptime(date_str, "%d/%m/%Y, %H:%M:%S")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = date_str

                        link = base_url

                        appender(title, group_name, description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
