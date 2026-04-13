"""
    Parser for Black Water group
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
        if filename.startswith('blackwater-'):
            html_doc = tmp_dir / filename
            file_md5 = extract_md5_from_filename(filename)
            base_url = find_slug_by_md5('black water', file_md5)
            
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                cards = soup.find_all('div', class_='card')
                for card in cards:
                    title_el = card.find('h5', class_='card-title')
                    if not title_el:
                        continue
                    
                    victim = title_el.get_text().strip()
                    
                    description = ""
                    published = ""
                    post_url = ""
                    
                    # Extract Publication Date
                    # <p class="card-text text-muted">Publicated at 2026-03-20 10:20:42</p>
                    date_p = card.find('p', string=re.compile(r'Publicated at', re.I))
                    if date_p:
                        date_str = date_p.get_text().replace("Publicated at", "").strip()
                        try:
                            published = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            pass
                    
                    # Extract Description
                    # The next p tag usually contains the description
                    desc_p = card.find('p', style=re.compile(r'webkit-line-clamp'))
                    if desc_p:
                        description = desc_p.get_text().strip()
                    
                    # Extract Post URL
                    # <a class="btn btn-secondary btn-sm" href="/blog?uuid=...">See more</a>
                    link_el = card.find('a', href=re.compile(r'^/blog\?uuid='))
                    if link_el:
                        post_url = link_el.get('href')
                        if base_url:
                            post_url = base_url.rstrip('/') + post_url

                    appender(
                        victim=victim,
                        group_name='black water',
                        description=description,
                        website="",
                        published=published,
                        post_url=post_url,
                        country=""
                    )

if __name__ == "__main__":
    main()
