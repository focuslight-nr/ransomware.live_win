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
    group_name = "pear"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f"Parsing: {html_doc}")
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                # Victims are in separate tables with box-shadow
                victim_tables = soup.find_all('table', style=re.compile(r'box-shadow: #bdbdbd'))
                
                for table in victim_tables:
                    try:
                        # Look for info block inside the table
                        info_div = table.find('div', class_='info')
                        if not info_div: continue
                        
                        # Description is often in td.es-text-7589 before the info div
                        desc_td = table.find('td', class_='es-text-7589')
                        description = ""
                        if desc_td:
                            # The first <p> might be the description
                            p_tag = desc_td.find('p')
                            if p_tag:
                                description = p_tag.get_text(strip=True)
                        
                        # Website
                        website = ""
                        site_label = info_div.find('strong', string=re.compile(r'Site:'))
                        if site_label:
                            site_a = site_label.find_next('a', href=True)
                            if site_a:
                                website = site_a.get_text(strip=True)
                        
                        # Victim name - use website or part of ID if name not found
                        victim_name = website.split('.')[0].capitalize() if website else "Unknown"
                        
                        # Details link
                        post_url = ""
                        details_a = info_div.find('a', href=re.compile(r'Companies/'))
                        if details_a:
                            post_url = urljoin(base_url + '/', details_a['href']) if base_url else details_a['href']

                        if website or description:
                            appender(victim_name, group_name, description, website, "", post_url)
                    except Exception as e:
                        errlog(f"{group_name} - table parse fail: {e}")
            except Exception as e:
                errlog(f"{group_name} - error reading file {filename}: {e}")

if __name__ == "__main__":
    main()
