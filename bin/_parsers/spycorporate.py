"""
    Parser for Spy Corporate -> appender()
    Signature: def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os
from bs4 import BeautifulSoup
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "spy corporate"
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('spycorporate-'):
                html_doc = tmp_dir / filename
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')
                    
                    # Find base_url for post link generation
                    try:
                        base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc)))
                    except Exception:
                        base_url = ""
                    
                    rows = soup.find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) < 5:
                            continue
                        
                        # Victim name is in 2nd td
                        title = tds[1].text.strip()
                        if not title:
                            continue
                        
                        # Description from revenue (3rd td) and downloads (5th td)
                        revenue = tds[2].text.strip()
                        downloads = tds[4].text.strip()
                        description = f"Revenue: {revenue}. Downloads: {downloads}."
                        
                        # Post URL from form inside 6th td
                        post_url = ""
                        form = row.find('form')
                        if form:
                            action = form.get('action', '')
                            q_input = form.find('input', {'name': 'q'})
                            q_val = q_input.get('value', '') if q_input else ''
                            if action and q_val:
                                rel_url = f"{action.strip('/')}?q={q_val}"
                                if base_url:
                                    post_url = f"{base_url.rstrip('/')}/{rel_url}"
                                else:
                                    post_url = rel_url
                        
                        # Call appender
                        appender(title, group_name, description=description, post_url=post_url)
                        
        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
