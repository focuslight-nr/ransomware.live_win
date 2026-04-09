"""
    Parser for Audit group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, datetime, sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, tmp_dir
from pathlib import Path

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('audit-'):
            html_doc = tmp_dir / filename
            # Extract MD5 to find the base URL (slug)
            file_md5 = extract_md5_from_filename(filename)
            base_url = find_slug_by_md5('audit', file_md5)
            
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    title_div = card.find('div', class_='title')
                    if not title_div:
                        continue
                    
                    victim = title_div.text.strip()
                    if victim == "[ COOPERATION REACHED ]":
                        # Skip redacted victims
                        continue
                    
                    # Extract URL from onclick
                    onclick = card.get('onclick', '')
                    post_url = ""
                    url_match = re.search(r"window\.open\('([^']+)'", onclick)
                    if url_match:
                        post_url = url_match.group(1)
                        if base_url and post_url.startswith('/'):
                            post_url = base_url.rstrip('/') + post_url
                    
                    # Extract Discovery Date
                    published = ""
                    meta_infos = card.find_all('div', class_='meta-info')
                    for info in meta_infos:
                        if "DISCOVERY DATE:" in info.text:
                            date_str = info.text.replace("DISCOVERY DATE:", "").strip()
                            try:
                                published = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass
                    
                    # Description
                    description = ""
                    status_div = card.find('div', class_=re.compile('status-.*'))
                    if status_div:
                        description = status_div.text.strip()

                    appender(
                        victim=victim,
                        group_name='audit',
                        description=description,
                        website="",
                        published=published,
                        post_url=post_url,
                        country=""
                    )

if __name__ == "__main__":
    main()
