"""
    Parser for TiMc group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |     X     |     X    |
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
        if filename.startswith('timc-'):
            html_doc = tmp_dir / filename
            file_md5 = extract_md5_from_filename(filename)
            base_url = find_slug_by_md5('timc', file_md5)
            
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                # Each victim card is in a div that contains an <a> with target="_blank"
                # Looking at the pattern:
                # <div ...>
                #   <div ...>
                #     <p class="... line-clamp-3">Description</p>
                #     <button>EXPAND</button>
                #   </div>
                #   <a href="https://..." ...>...</a>
                #   <div ...>
                #     <div ...>
                #        <span ...>DEADLINE: <span ...>2026-04-15 11:32:00</span></span>
                #     </div>
                #   </div>
                # </div>
                
                # Let's find all external links first as they are good anchors for victim cards
                external_links = soup.find_all('a', href=re.compile(r'^https?://'))
                for link in external_links:
                    victim = link.get_text().strip()
                    if not victim:
                        continue
                    victim = victim.rstrip('/')
                    website = victim
                    
                    description = ""
                    published = ""
                    
                    # The description is usually in a <p> in a sibling div above the <a>
                    container = link.find_parent('div', recursive=False) or link.parent
                    
                    # Search for description in surrounding elements
                    # Based on HTML structure, it might be in a preceding div
                    prev_div = link.find_previous_sibling('div')
                    if prev_div:
                        desc_p = prev_div.find('p', class_=re.compile(r'line-clamp'))
                        if desc_p:
                            description = desc_p.get_text().strip()
                    
                    # Search for deadline in succeeding elements
                    next_div = link.find_next_sibling('div')
                    if next_div:
                        deadline_span = next_div.find('span', string=re.compile(r'DEADLINE:', re.I))
                        if not deadline_span:
                            # Search deeper
                            deadline_span = next_div.find(lambda tag: tag.name == "span" and "DEADLINE:" in tag.get_text())
                        
                        if deadline_span:
                            # The actual date is often in a nested span or the next span
                            date_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', next_div.get_text())
                            if date_match:
                                date_str = date_match.group(0)
                                try:
                                    published = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    pass

                    appender(
                        victim=victim,
                        group_name='timc',
                        description=description,
                        website=website,
                        published=published,
                        post_url=base_url,
                        country=""
                    )

if __name__ == "__main__":
    main()
