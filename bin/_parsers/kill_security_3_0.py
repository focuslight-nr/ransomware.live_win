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

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "killsecurity3.0"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f"Parsing: {html_doc}")
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, "html.parser")
                
                # Victim cards are in divs with h-[200px] class
                victim_divs = soup.find_all('div', class_=re.compile(r'h-\[200px\]'))
                
                if victim_divs:
                    stdlog(f"Found {len(victim_divs)} victim cards for {group_name}")
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
                            errlog(f"{group_name} - entry parse fail: {e}")
                else:
                    errlog(f"{group_name} - no victim cards found in {filename}")
            except Exception as e:
                errlog(f"{group_name} - error reading file {filename}: {e}")

if __name__ == "__main__":
    main()
