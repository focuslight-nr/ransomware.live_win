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
        if filename.startswith("payouts king-"):
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
                # The site uses two rows per victim (one for summary, one for expandable info)
                # But we can iterate through all rows and pick the ones with ID
                for row in rows:
                    if not row.has_attr('id') or row.get('id') == 'table':
                        continue
                    
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 4: continue

                        # Column 0: Company name (p tag with title class)
                        title_p = row.find('p', class_=re.compile(r'_title_'))
                        victim = title_p.get_text(strip=True) if title_p else cells[0].get_text(strip=True)
                        
                        # Column 1: Created date
                        published = cells[1].get_text(strip=True)
                        if published:
                            try:
                                published_dt = datetime.strptime(published, '%Y-%m-%d')
                                published = published_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass

                        # Column 2: Website
                        website = cells[2].get_text(strip=True)
                        
                        # Column 3: Country
                        country = cells[3].get_text(strip=True)

                        # Look ahead or lookup associated info row for description
                        description = ""
                        post_url = ""
                        
                        # Find the next sibling row with class 'infoRow'
                        info_row = row.find_next_sibling('tr', class_='infoRow')
                        if info_row:
                            # About company
                            desc_span = info_row.find('span', class_=re.compile(r'_value_'))
                            if desc_span:
                                description = desc_span.get_text(strip=True)
                            
                            # Full info link
                            info_link = info_row.find('a', href=True)
                            if info_link:
                                post_url = urljoin(base_url, info_link['href']) if base_url else info_link['href']

                        appender(victim, target_group, description, website, published, post_url, country)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing row: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

