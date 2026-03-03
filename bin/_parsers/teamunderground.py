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
    group_name = "teamunderground"
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

                # Items are in div.col-lg-6.col-12.mb-3
                items = soup.find_all('div', class_=re.compile(r'col-lg-6.*mb-3'))
                
                for item in items:
                    try:
                        filling = item.find('div', class_='filling')
                        if not filling:
                            continue
                        
                        # Link
                        link_tag = filling.find('a', class_='stretched-link')
                        link = urljoin(base_url, link_tag['href']) if link_tag and base_url else ""

                        # Extract info from block__info divs
                        name = ""
                        revenue = ""
                        v_type = ""
                        country = ""
                        date_str = ""
                        size = ""

                        info_blocks = filling.find_all('div', class_='block__info')
                        for block in info_blocks:
                            rows = block.find_all('div')
                            for row in rows:
                                span = row.find('span')
                                p = row.find('p')
                                if not span or not p:
                                    continue
                                
                                label = span.get_text(strip=True).lower()
                                value = p.get_text(strip=True)

                                if 'name' in label:
                                    name = value
                                elif 'revenue' in label:
                                    revenue = value
                                elif 'type' in label:
                                    v_type = value
                                elif 'ountry' in label: # Use partial match for 'Country' due to special chars
                                    country = value
                                elif 'date' in label:
                                    date_str = value
                                elif 'size' in label:
                                    size = value

                        if not name:
                            continue

                        # Description
                        desc_parts = []
                        if revenue: desc_parts.append(f"Revenue: {revenue}")
                        if v_type: desc_parts.append(f"Type: {v_type}")
                        if size: desc_parts.append(f"Size: {size}")
                        description = " | ".join(desc_parts)

                        # Date formatting
                        published = ""
                        if date_str:
                            try:
                                # Format: 06/25/2025 08:19
                                dt = datetime.strptime(date_str, "%m/%d/%Y %H:%M")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        appender(name, group_name, description, '', published, link, country)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
