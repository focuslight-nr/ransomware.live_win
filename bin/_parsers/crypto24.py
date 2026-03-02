import os, datetime, sys, re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "crypto24"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f"Parsing: {html_doc}")
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Cards
                cards = soup.find_all('div', class_='ant-card')
                if cards:
                    stdlog(f"Found {len(cards)} cards for {group_name}")
                    for card in cards:
                        try:
                            # Title
                            title_h2 = card.find('h2')
                            if not title_h2: continue
                            victim = title_h2.get_text(strip=True)
                            
                            # Description
                            desc_p = card.find('p', style=re.compile(r'color: rgb\(221, 221, 221\)'))
                            description = desc_p.get_text(strip=True) if desc_p else ""
                            
                            # Country
                            country = ""
                            country_span = card.find('span', style=re.compile(r'color: rgb\(204, 204, 204\)'))
                            if country_span:
                                country = country_span.get_text(strip=True)
                            
                            # Website - often the title or hidden
                            website = ""
                            if "." in victim:
                                website = victim
                            
                            appender(victim, group_name, description, website, "", "", country)
                        except Exception as e:
                            errlog(f"{group_name} - card parse fail: {e}")
                else:
                    errlog(f"{group_name} - no cards found in {filename}")
            except Exception as e:
                errlog(f"{group_name} - error reading file {filename}: {e}")

if __name__ == "__main__":
    main()
