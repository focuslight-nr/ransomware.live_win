import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse, parse_qs

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "ms13"
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

                # Items are in divs with class post
                items = soup.find_all('div', class_='post')
                
                for item in items:
                    try:
                        # Title and Website
                        title_block = item.find('div', class_='post-title-block')
                        if not title_block:
                            continue
                        
                        name_div = title_block.find('div')
                        if not name_div:
                            continue
                        
                        full_title = name_div.get_text(strip=True)
                        # Example: uro.com (USA, Virginia)
                        title = full_title.split('(')[0].strip()
                        country = ""
                        if '(' in full_title:
                            country = full_title.split('(')[1].split(')')[0].strip()

                        website = ""
                        if '.' in title and ' ' not in title:
                            website = title

                        # Description
                        description = ""
                        text_div = item.find('div', class_='post-text')
                        if text_div:
                            description = text_div.get_text(strip=True)

                        # Status
                        status = ""
                        meter = item.find('div', class_='meter')
                        if meter:
                            status_span = meter.find('span')
                            if status_span:
                                status = status_span.get_text(strip=True)
                        
                        if status:
                            description = f"[{status}] {description}"

                        # Link
                        link = ""
                        more_link = item.find('a', class_='post-more-link')
                        if more_link and more_link.has_attr('onclick'):
                            onclick = more_link['onclick']
                            # location.href='/cl/clicks.php?uri=URO/index.html'
                            match = re.search(r"href='(.*?)'", onclick)
                            if match:
                                rel_link = match.group(1)
                                link = urljoin(base_url, rel_link)
                        
                        if not link:
                            link = base_url

                        appender(title, group_name, description, website, '', link, country)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
