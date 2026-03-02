"""
    Parser for Dragon Force (HTML Version)
"""

import os
import json
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime
import re

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "dragonforce"
    for filename in os.listdir(tmp_dir):
        if filename.startswith("dragonforce-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Dragon Force uses Nuxt 3, data is in a script tag
                script_tag = soup.find('script', id='__NUXT_DATA__')
                if script_tag:
                    try:
                        data = json.loads(script_tag.string)
                        # Nuxt 3 data format is a list of values
                        # Objects are represented by indices into this list
                        if isinstance(data, list) and len(data) > 0:
                            # We look for entries that look like a publication
                            # Typically: {"uuid": index, "name": index, "website": index, ...}
                            for item in data:
                                if isinstance(item, dict) and "name" in item and "uuid" in item:
                                    # Resolve index values
                                    def resolve(idx):
                                        if isinstance(idx, int) and 0 <= idx < len(data):
                                            return data[idx]
                                        return idx

                                    victim = str(resolve(item.get('name', '')))
                                    website = str(resolve(item.get('website', '')))
                                    description = str(resolve(item.get('description', '')))
                                    created_at = str(resolve(item.get('created_at', '')))
                                    
                                    # Skip if victim name is not a string or looks like an index still
                                    if not victim or victim == "name": continue
                                    
                                    published = ""
                                    if created_at:
                                        try:
                                            # Nuxt dates are often ISO strings
                                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                            published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                        except:
                                            published = created_at

                                    appender(victim, target_group, description, website, published)
                    except Exception as e:
                        errlog(f'{target_group} - JSON parse error: {e}')
                
                # Legacy fallback
                items = soup.find_all('div', class_='publications-list__publication')
                for item in items:
                    try:
                        name_tag = item.find('h3', class_='list-publication__name')
                        if not name_tag: continue
                        victim = name_tag.get_text(strip=True)
                        # ... (rest of legacy logic if needed)
                        appender(victim, target_group)
                    except:
                        pass
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

