import os, datetime, sys, re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from datetime import datetime
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = 'underground'
    stdlog(f"Processing group: {group_name}")
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith('teamunderground-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(group_name, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                # Cards are in a grid
                items = soup.find_all('div', class_='col-lg-6')
                if not items:
                    items = soup.find_all('div', class_='col-md-4')

                stdlog(f"Found {len(items)} items for {group_name}")
                for item in items:
                    try:
                        # Extract Name
                        name_span = item.find('span', string=re.compile(r'Name:', re.I))
                        if not name_span: continue
                        victim = name_span.find_next('p').get_text(strip=True)
                        
                        # Extract Website / Info
                        description = ""
                        info_divs = item.find_all('div')
                        for info in info_divs:
                            span = info.find('span')
                            p = info.find('p')
                            if span and p:
                                description += f"{span.get_text(strip=True)} {p.get_text(strip=True)}; "
                        
                        # Extract Link
                        post_url = ""
                        link_a = item.find('a', class_='stretched-link')
                        if link_a:
                            post_url = urljoin(base_url + '/', link_a['href']) if base_url else link_a['href']
                        
                        appender(victim, group_name, description, "", "", post_url)
                    except Exception as e:
                        errlog(f'{group_name} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
