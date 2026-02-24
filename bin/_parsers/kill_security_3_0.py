"""
    Kill Security 3.0 Parser
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
    group_name = "kill security 3.0"

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            with open(html_doc, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                
                # The HTML structure for Kill Security 3.0
                # <div class="... h-[200px] ...">
                #   ...
                #   <span class="... text-xl ...">Victim Name</span>
                #   <span class="... text-[10px] ...">website.com</span>
                #   ...
                #   <div class="flex-1 ...">Description</div>
                # </div>
                
                # Search for divs that likely contain victim cards
                victim_divs = soup.find_all('div', class_=re.compile(r'h-\[200px\]'))
                
                if victim_divs:
                    stdlog(f"Found {len(victim_divs)} victim cards for {group_name} in {filename}")
                    
                    for div in victim_divs:
                        try:
                            # Title
                            title_span = div.find('span', class_=re.compile(r'text-xl'))
                            title = title_span.text.strip() if title_span else ""
                            
                            # Website
                            website_span = div.find('span', class_=re.compile(r'text-\[10px\]'))
                            website = website_span.text.strip() if website_span else ""
                            
                            # Description
                            desc_div = div.find('div', class_=re.compile(r'flex-1'))
                            description = desc_div.text.strip() if desc_div else ""
                            
                            if not title and website:
                                title = website
                            
                            if title:
                                appender(title, group_name, description, website)
                        except Exception as e:
                            errlog(f"{group_name} - entry parse fail: {e} in file: {filename}")
                else:
                    # Try a different approach if no h-[200px] found
                    # Maybe it's a different version or structure
                    pass

if __name__ == "__main__":
    main()
