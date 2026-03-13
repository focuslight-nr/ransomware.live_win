"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, datetime, sys
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, tmp_dir
from pathlib import Path

def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('cipherforce-'):
                html_doc = tmp_dir / filename
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Find the slug/base URL
                group_name = 'cipherforce'
                target_md5 = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5(group_name, target_md5)
                if not base_url:
                    base_url = "http://22evxpggnkyrxpluewqsrv5j4jtde6hut2peq3w44d6ase676qlkoead.onion" # Fallback

                victim_cards = soup.find_all('div', class_='victim-card')
                for card in victim_cards:
                    name_link = card.find('h3', class_='victim-name').find('a')
                    if not name_link:
                        continue
                    name = name_link.text.strip()
                    link = name_link['href']
                    if link.startswith('/'):
                        link = base_url + link
                    # Meta items: Industry, Country
                    meta_items = card.find('div', class_='victim-meta').find_all('span', class_='meta-item')
                    country = ""
                    industry = ""
                    for item in meta_items:
                        text = item.text.strip()
                        if len(text) == 2 and text.isupper():
                            country = text
                        else:
                            industry = text

                    description = ""
                    if country:
                        description = f"Country : {country}"
                    if industry:
                        if description:
                            description += f" - Industry: {industry}"
                        else:
                            description = f"Industry: {industry}"

                    # Published / Deadline
                    published = ""
                    countdown = card.find('div', class_='countdown-timer')
                    if countdown and countdown.has_attr('data-deadline'):
                        deadline_str = countdown['data-deadline']
                        try:
                            # 2026-03-25T17:00:00Z -> 2026-03-25 17:00:00.000000
                            dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                            published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            published = deadline_str.replace('Z', '').replace('T', ' ')
                    
                    if not published:
                        published = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                    appender(
                        victim=name,
                        group_name=group_name,
                        description=description, # AI will enrich
                        website="",      # AI will guess
                        published=published,
                        post_url=link,
                        country=country
                    )
        except Exception as e:
            errlog('cipherforce - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
