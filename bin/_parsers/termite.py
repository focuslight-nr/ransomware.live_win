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
    group_name = "termite"
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

                # Items are <a> tags with min-h-36 class
                items = soup.find_all('a', class_='min-h-36')
                
                for item in items:
                    try:
                        # Website
                        h2 = item.find('h2', class_='font-bold')
                        website = h2.get_text(strip=True) if h2 else ""

                        # Company name
                        h3 = item.find('h3', class_='text-sm')
                        title = h3.get_text(strip=True) if h3 else website
                        
                        if not title:
                            continue

                        # Link
                        link = urljoin(base_url, item['href']) if base_url else item['href']

                        # Date
                        published = ""
                        date_div = item.find('div', class_=re.compile(r'items-end'))
                        if date_div:
                            date_str = date_div.get_text(strip=True)
                            try:
                                # Format: 03/03/2026, 10:05:25
                                dt = datetime.strptime(date_str, "%d/%m/%Y, %H:%M:%S")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        description = f"Leaked data from {group_name} group."
                        
                        appender(title, group_name, description, website, published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
