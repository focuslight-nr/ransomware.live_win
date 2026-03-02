import os, datetime, sys, re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "sarcoma"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f"Parsing: {html_doc}")
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Victim cards
                cards = soup.find_all('div', class_='sg-form')
                if cards:
                    stdlog(f"Found {len(cards)} entries for {group_name}")
                    for card in cards:
                        try:
                            title_div = card.find('div', class_='card-title')
                            if not title_div: continue
                            victim = title_div.get_text(strip=True)
                            
                            if victim.lower() in ('contacts', 'about us', 'main'):
                                continue

                            description = ""
                            desc_div = card.find('div', class_='card-text')
                            if desc_div:
                                description = desc_div.get_text(strip=True)
                            
                            appender(victim, group_name, description)
                        except Exception as e:
                            errlog(f"{group_name} - card parse fail: {e}")
                
                # Also try modals
                modals = soup.find_all('div', class_='modal-content')
                for modal in modals:
                    try:
                        title_h5 = modal.find('h5')
                        if not title_h5: continue
                        victim = title_h5.get_text(strip=True)
                        
                        if victim.lower() in ('contacts', 'about us'):
                            continue
                            
                        pre_desc = modal.find('pre', class_='text-break')
                        description = pre_desc.get_text(strip=True) if pre_desc else ""
                        
                        appender(victim, group_name, description)
                    except:
                        pass
            except Exception as e:
                errlog(f"{group_name} - error reading file {filename}: {e}")

if __name__ == "__main__":
    main()
