"""
    From Template v4 - 202412827
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
        try:
            if filename.startswith('exitium-'):
                html_doc = tmp_dir / filename
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Find the slug/base URL
                group_name = 'exitium'
                target_md5 = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5(group_name, target_md5)
                if not base_url:
                    base_url = "http://m3ksukzn2glzfdvlusohril7n3iyk4z4fudf6mm22lwhpbpt5aiee5qd.onion" # Fallback

                target_cards = soup.find_all('div', class_='target-card')
                for card in target_cards:
                    # Name
                    title_el = card.find('h3', class_='target-title')
                    if not title_el:
                        continue
                    name = title_el.text.strip()
                    
                    # Description
                    text_el = card.find('p', class_='target-text')
                    description = text_el.text.strip() if text_el else ""
                    
                    # Website estimation from description (zoominfo/pic)
                    website = ""
                    zoominfo_match = re.search(r'https://www\.zoominfo\.com/(?:c|pic)/([^/\s]+)', description)
                    if zoominfo_match:
                        website = zoominfo_match.group(1).replace('-', '.')
                    
                    # Published date
                    published = ""
                    # Check for countdown timer (pending)
                    countdown = card.find('div', class_='time')
                    if countdown and countdown.has_attr('data-publish-date'):
                        pub_date_str = countdown['data-publish-date']
                        try:
                            # 2026-03-23T18:40:33.214861
                            dt = datetime.fromisoformat(pub_date_str)
                            published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            published = pub_date_str.replace('T', ' ')
                    
                    if not published:
                        published = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                    # Country/Industry heuristics from description
                    # Use "Country : " format for shared_utils
                    if "Brasil" in description:
                        description = "Country : BR - " + description
                    
                    appender(
                        victim=name,
                        group_name=group_name,
                        description=description,
                        website=website,
                        published=published,
                        post_url=base_url, # No specific post URL found in overview
                        country="" # Let appender handle it from description
                    )
        except Exception as e:
            errlog('exitium - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
