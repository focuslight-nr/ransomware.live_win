"""
    Tengu Parser
    From Template v4 - 202412827
"""

import os, datetime, sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME")
tmp_dir = Path(home + os.getenv("TMP_DIR"))

def main():
    group_name = "tengu"

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                
                # The HTML structure for Tengu
                # <div class="post-card" onclick="window.location='/blog/...' ">
                #   <div class="post-header">
                #     <div class="post-title">Victim Name</div>
                #   </div>
                #   <div class="post-body">Description</div>
                # </div>
                
                post_cards = soup.find_all('div', class_='post-card')
                if post_cards:
                    stdlog(f"Found {len(post_cards)} post cards for {group_name} in {filename}")
                    
                    # Try to get base URL if possible
                    target_md5 = extract_md5_from_filename(filename)
                    base_url = find_slug_by_md5(group_name, target_md5)
                    if base_url:
                        base_url = base_url.rstrip('/')
                    else:
                        base_url = ""

                    for card in post_cards:
                        try:
                            title_tag = card.find('div', class_='post-title')
                            title = title_tag.text.strip() if title_tag else ""
                            
                            description_tag = card.find('div', class_='post-body')
                            description = description_tag.text.strip() if description_tag else ""
                            
                            # Extract link from onclick attribute
                            # onclick="window.location='/blog/.../'"
                            onclick = card.get('onclick', '')
                            link_match = re.search(r"window\.location='(.*?)'", onclick)
                            link = link_match.group(1) if link_match else ""
                            
                            if link.startswith('/') and base_url:
                                full_link = base_url + link
                            else:
                                full_link = link
                            
                            if title:
                                appender(title, group_name, description, '', '', full_link)
                        except Exception as e:
                            errlog(f"{group_name} - entry parse fail: {e} in file: {filename}")
                else:
                    # errlog(f"{group_name} - no items found in file: {filename}")
                    pass

if __name__ == "__main__":
    main()
