"""
    Parser for ShadowByt3$ group
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
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog, tmp_dir
from pathlib import Path

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('shadowbyt3$-'):
            html_doc = tmp_dir / filename
            file_md5 = extract_md5_from_filename(filename)
            base_url = find_slug_by_md5('shadowbyt3$', file_md5)
            
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                
                # Check if this is the leaks page (has <h1>☠ ShadowByt3$ LEAKS ☠</h1>)
                h1 = soup.find('h1')
                if not h1 or "LEAKS" not in h1.get_text():
                    # Check if it's the landing page
                    hero = soup.find('section', class_='hero')
                    if hero and "ShadowByt3$" in hero.get_text():
                        stdlog(f"shadowbyt3$ - skipping landing page: {filename}")
                    continue

                cards = soup.find_all('div', class_='card')
                for card in cards:
                    h3 = card.find('h3')
                    if not h3:
                        continue
                        
                    victim = h3.get_text().strip()
                    # Skip administrative entries if any
                    if victim == "PGP_Verified_Public_key":
                        continue
                    
                    description = ""
                    published = ""
                    post_url = base_url if base_url else ""
                    
                    # Extract Release date
                    # <p><strong>Release:</strong> 2026-04-05 21:09:00</p>
                    release_p = card.find('p', string=re.compile(r'Release:', re.I))
                    if not release_p:
                        # Try searching in all p tags
                        for p in card.find_all('p'):
                            if "Release:" in p.get_text():
                                release_p = p
                                break
                    
                    if release_p:
                        date_str = release_p.get_text().replace("Release:", "").strip()
                        try:
                            published = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            pass
                    
                    # Extract download link for post_url
                    # <a id="download_64" href="download_handler.php?id=64" ...>
                    download_link = card.find('a', id=re.compile(r'download_'))
                    if download_link and download_link.get('href'):
                        href = download_link.get('href')
                        if base_url:
                            # Use the base URL and append the handler
                            # If base_url already contains leaks.php, we might need to be careful
                            # Let's assume the base_url is the root or we clean it
                            root_url = base_url.split('/leaks.php')[0]
                            post_url = root_url.rstrip('/') + '/' + href.lstrip('/')

                    appender(
                        victim=victim,
                        group_name='shadowbyt3$',
                        description=description,
                        website="",
                        published=published,
                        post_url=post_url,
                        country=""
                    )

if __name__ == "__main__":
    main()
