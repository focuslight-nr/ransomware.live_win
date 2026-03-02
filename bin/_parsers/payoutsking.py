"""
    Parser for Payouts King
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime
import re

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "payoutsking"
    for filename in os.listdir(tmp_dir):
        if filename.startswith("payoutsking-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL to reconstruct links if possible
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                # Find table body
                table_body = soup.find('tbody', id='table')
                if not table_body:
                    # Alternative lookup by class or structure
                    table_body = soup.find('tbody')
                
                if not table_body:
                    errlog(f'{target_group} - table body not found')
                    continue

                # Process rows
                rows = table_body.find_all('tr')
                # The site uses rows for victims. Some might be expandable.
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 2: continue
                    
                    try:
                        # Column 0: Company name (p tag with title class)
                        title_p = row.find('p', class_=re.compile(r'_title_'))
                        if not title_p:
                            # Fallback to the first cell text
                            victim = cells[0].get_text(strip=True)
                        else:
                            victim = title_p.get_text(strip=True)
                        
                        if not victim or victim.lower() == "company": continue

                        # Column 1: Created date
                        published = cells[1].get_text(strip=True)
                        if published:
                            try:
                                # Format might be YYYY-MM-DD
                                published_dt = datetime.strptime(published, '%Y-%m-%d')
                                published = published_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass

                        # Column 2: Website
                        website = ""
                        if len(cells) > 2:
                            website = cells[2].get_text(strip=True)
                        
                        # Column 3: Country
                        country = ""
                        if len(cells) > 3:
                            country = cells[3].get_text(strip=True)

                        # Description and link are sometimes in dynamic expandable areas
                        description = ""
                        post_url = ""
                        
                        # Check for a "data-description" or info sibling
                        info_row = row.find_next_sibling('tr')
                        if info_row and not info_row.find('td', recursive=False):
                             # This might be an info block
                             desc_el = info_row.find(class_=re.compile(r'_description_|_value_'))
                             if desc_el:
                                 description = desc_el.get_text(strip=True)
                             
                             link_el = info_row.find('a', href=True)
                             if link_el:
                                 post_url = urljoin(base_url, link_el['href']) if base_url else link_el['href']

                        appender(victim, target_group, description, website, published, post_url, country)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing row: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

