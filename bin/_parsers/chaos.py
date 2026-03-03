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
    group_name = "chaos"
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

                # The HTML structure has victim items in cards with class bg-bunker
                items = soup.find_all('div', class_=re.compile(r'bg-bunker'))
                
                for item in items:
                    try:
                        # Skip blurred items (randomized strings during countdown)
                        title_div = item.find('div', class_=re.compile(r'text-lg font-bold'))
                        if not title_div or 'blur-xs' in title_div.get('class', []):
                            continue
                        
                        title_tag = title_div.find('a')
                        if not title_tag:
                            title = title_div.get_text(strip=True)
                            link = base_url
                        else:
                            title = title_tag.get_text(strip=True)
                            link = base_url + title_tag['href']

                        # Extract website
                        website = ""
                        # Website is usually the second link in the item or in a specific div
                        links = item.find_all('a', href=True)
                        for l in links:
                            if l['href'].startswith('http') and group_name not in l['href']:
                                website = l['href']
                                break

                        # Extract description and size
                        description = ""
                        desc_div = item.find('div', class_=re.compile(r'break-words'))
                        if desc_div and 'blur-xs' not in desc_div.get('class', []):
                            description = desc_div.get_text(strip=True)

                        # Extract size
                        size_tag = item.find('span', class_='font-bold')
                        if size_tag:
                            size_val = size_tag.get_text(strip=True)
                            description = f"[{size_val}] {description}"

                        appender(title, group_name, description, website, '', link)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
