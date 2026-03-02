"""
    Parser for Ransom House
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
import re

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "ransomhouse"
    for filename in os.listdir(tmp_dir):
        if filename.startswith("ransomhouse-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                records = soup.find_all('div', class_='cls_record')
                for record in records:
                    try:
                        top_div = record.find('div', class_='cls_recordTop')
                        if not top_div:
                            continue
                        victim = top_div.get_text(strip=True)

                        website = ""
                        middle_div = record.find('div', class_='cls_recordMiddle')
                        if middle_div:
                            website = middle_div.get_text(strip=True)

                        post_url = ""
                        link_a = record.find('a', href=True)
                        if link_a:
                            post_url = urljoin(base_url, link_a['href']) if base_url else link_a['href']

                        # Date extraction from "Action date:"
                        published = ""
                        bottom_elements = record.find_all('div', class_='cls_recordBottomElement')
                        for element in bottom_elements:
                            label_div = element.find('div', class_='cls_headerSmall')
                            if label_div and "Action date" in label_div.get_text():
                                # The date is in the next div
                                val_div = label_div.find_next_sibling('div')
                                if val_div:
                                    published_str = val_div.get_text(strip=True)
                                    try:
                                        # Convert DD/MM/YYYY to YYYY-MM-DD
                                        from datetime import datetime
                                        dt = datetime.strptime(published_str, "%d/%m/%Y")
                                        published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                    except:
                                        published = published_str
                                break

                        appender(victim, target_group, "", website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing record: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

