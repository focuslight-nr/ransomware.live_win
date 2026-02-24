"""
    Space Bears Parser
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
    group_name = "spacebears"

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                
                # The HTML structure for Space Bears
                # <div class="companies-list__item">
                #   <div class="content">
                #     <div class="name">
                #       <a href="...">Victim Name</a>
                #     </div>
                #     <div class="text">
                #       <p>Description</p>
                #       <p><a href="...">website.com</a></p>
                #     </div>
                #   </div>
                # </div>
                
                items = soup.find_all('div', class_='companies-list__item')
                if items:
                    stdlog(f"Found {len(items)} items for {group_name} in {filename}")
                    
                    for item in items:
                        try:
                            name_div = item.find('div', class_='name')
                            if name_div:
                                link_tag = name_div.find('a')
                                if link_tag:
                                    title = link_tag.text.strip()
                                    post_url = link_tag.get('href', '')
                                else:
                                    title = name_div.text.strip()
                                    post_url = ""
                            else:
                                continue

                            text_div = item.find('div', class_='text')
                            description = ""
                            website = ""
                            if text_div:
                                # Look for website link inside text div
                                website_tag = text_div.find('a')
                                if website_tag:
                                    website = website_tag.text.strip()
                                
                                # Use all p tags for description
                                p_tags = text_div.find_all('p')
                                description = " ".join(p.text.strip() for p in p_tags if p.text.strip() != website)

                            if title:
                                appender(title, group_name, description, website, '', post_url)
                        except Exception as e:
                            errlog(f"{group_name} - entry parse fail: {e} in file: {filename}")
                else:
                    # errlog(f"{group_name} - no items found in file: {filename}")
                    pass

if __name__ == "__main__":
    main()
