import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "radar"
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

                # The HTML structure uses Ant Design List items for news
                items = soup.find_all('li', class_='ant-list-item')
                
                for item in items:
                    try:
                        # Extract title from the news link
                        title_tag = item.find('h4', class_='ant-list-item-meta-title')
                        if not title_tag:
                            continue
                        a_tag = title_tag.find('a')
                        if not a_tag:
                            continue
                        title = a_tag.get_text(strip=True)

                        # Extract link
                        link = ""
                        if base_url:
                            link = base_url + a_tag['href']

                        # Extract date
                        published = ""
                        date_tag = item.find('span', class_=re.compile(r'_dateTime'))
                        if date_tag:
                            date_str = date_tag.get_text(strip=True)
                            try:
                                # Format example: "03/08/2025, 21:31:16"
                                parsed_date = datetime.strptime(date_str, "%d/%m/%Y, %H:%M:%S")
                                published = parsed_date.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        description = "News item from Radar group platform."
                        
                        appender(title, group_name, description, '', published, link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
