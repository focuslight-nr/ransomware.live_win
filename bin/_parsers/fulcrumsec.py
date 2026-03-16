"""
    Parser for FulcrumSec Ransomware Group
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, tmp_dir, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from urllib.parse import urljoin

def main():
    group_name = "fulcrumsec"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f'{group_name}-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Extract MD5 and base URL
                md5_val = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5(group_name, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')
                
                # FulcrumSec uses a card-grid for major victims
                card_grid = soup.find('div', class_='card-grid')
                if card_grid:
                    cards = card_grid.find_all('a', class_='card')
                    for card in cards:
                        try:
                            # Victim name is usually in the alt attribute of the logo
                            img_tag = card.find('img')
                            victim = img_tag['alt'] if img_tag and img_tag.has_attr('alt') else "Unknown"
                            
                            # Link is in the href
                            link = card['href']
                            post_url = urljoin(base_url, link) if base_url else link
                            
                            appender(victim, group_name, "", "", "", post_url)
                        except Exception as e:
                            errlog(f'{group_name} - error parsing card: {e}')

                # Also handle the /shame/ link if it's considered a secondary list
                # (In this specific case, the cards seem to be the primary focus)
                
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
