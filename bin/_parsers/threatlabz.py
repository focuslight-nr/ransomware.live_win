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
    group_name = "threatlabz"
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

                # Items are in a tags with MuiLink-root class
                items = soup.find_all('a', class_=re.compile(r'MuiLink-root'))
                
                for item in items:
                    try:
                        boxes = item.find_all('div', class_='MuiBox-root', recursive=False)
                        if len(boxes) < 2:
                            continue
                        
                        # Name
                        name_tag = boxes[0].find('p')
                        if not name_tag:
                            continue
                        title = name_tag.get_text(strip=True)

                        # Dates
                        published = ""
                        update_info = ""
                        date_ps = boxes[1].find_all('p')
                        for p in date_ps:
                            text = p.get_text(strip=True)
                            if 'CREATE:' in text:
                                date_str = text.replace('CREATE:', '').strip()
                                try:
                                    # Format: 2026.01.28
                                    dt = datetime.strptime(date_str, "%Y.%m.%d")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = date_str
                            elif 'UPDATE:' in text:
                                update_info = text

                        description = update_info
                        
                        # Link
                        link = urljoin(base_url, item['href']) if base_url else item['href']

                        appender(title, group_name, description, '', published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
