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
    group_name = "killsecurity3.0"
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

                # The HTML structure has victim items in rounded bordered divs
                # We can look for divs that contain both a company name and a domain
                items = soup.find_all('div', class_=re.compile(r'flex flex-col.*rounded-\[10px\]'))
                
                for item in items:
                    try:
                        # Extract company name
                        name_tag = item.find('span', class_=re.compile(r'text-white/75.*text-xl'))
                        if not name_tag:
                            continue
                        title = name_tag.get_text(strip=True)

                        # Extract website
                        website = ""
                        website_tag = item.find('span', class_=re.compile(r'text-white/40.*text-\[10px\]'))
                        if website_tag:
                            website = website_tag.get_text(strip=True)

                        # Extract description
                        description = ""
                        desc_tag = item.find('div', class_=re.compile(r'flex-1.*text-xs'))
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)
                            if description == "No description given.":
                                description = ""

                        # Extract country from flag alt attribute
                        country = ""
                        flag_img = item.find('img', alt=re.compile(r'flag'))
                        if flag_img:
                            country = flag_img['alt'].replace(' flag', '').upper()

                        # Extract status
                        published = ""
                        status_tag = item.find('div', class_=re.compile(r'text-right.*text-\[11px\]'))
                        if status_tag:
                            published = status_tag.get_text(strip=True)

                        # Link
                        link = base_url

                        appender(title, group_name, description, website, published, link, country)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
