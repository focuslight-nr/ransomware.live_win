"""
    Parser for Lamashtu group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |     X     |     X    |
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
        if filename.startswith('lamashtu-'):
            html_doc = tmp_dir / filename
            file_md5 = extract_md5_from_filename(filename)
            base_url = find_slug_by_md5('lamashtu', file_md5)
            
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                cards = soup.find_all('a', class_='card')
                for card in cards:
                    title_el = card.find('h3', class_='card-title')
                    if not title_el:
                        continue
                    
                    victim = title_el.get_text().strip()
                    
                    description = ""
                    published = ""
                    post_url = ""
                    
                    # Extract URL
                    href = card.get('href')
                    if href and base_url:
                        post_url = base_url.rstrip('/') + href
                    
                    # Extract Description
                    desc_el = card.find('p', class_='card-description')
                    if desc_el:
                        description = desc_el.get_text().strip()
                    
                    # Extract Date
                    # The date is in a div with class "meta-item" and often has a label-mono span
                    # <div class="meta-item _nhkqt0"><span class="label-mono _nhkqt0">// PUBLISHED</span> <span class="_nhkqt0">2026-04-14</span></div>
                    meta_items = card.find_all('div', class_='meta-item')
                    for item in meta_items:
                        if "// PUBLISHED" in item.get_text():
                            # The date is usually in the second span or the text following the first span
                            spans = item.find_all('span')
                            if len(spans) >= 2:
                                date_str = spans[1].get_text().strip()
                                try:
                                    # site date format is YYYY-MM-DD
                                    published = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    pass

                    appender(
                        victim=victim,
                        group_name='lamashtu',
                        description=description,
                        website="",
                        published=published,
                        post_url=post_url,
                        country=""
                    )

if __name__ == "__main__":
    main()
