"""
    Icarus Parser
    Extracts victim data from Icarus ransomware group pages.
"""

import os, datetime, sys, re, json
from bs4 import BeautifulSoup
from datetime import datetime
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
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('icarus-') and filename.endswith('.html'):
                html_doc = tmp_dir / filename
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file, 'html.parser')
                    
                    # Try to extract from victimsData script first as it's more complete
                    script_tag = soup.find('script', string=re.compile('var victimsData ='))
                    if script_tag:
                        script_content = script_tag.string
                        # Extract the JSON array using regex
                        match = re.search(r'var victimsData = (\[.*?\]);', script_content, re.DOTALL)
                        if match:
                            try:
                                victims_data = json.loads(match.group(1))
                                for victim in victims_data:
                                    name = victim.get('name', '').strip()
                                    description = victim.get('description', '').strip()
                                    size = victim.get('size_gb', '')
                                    
                                    # Use countdown_end as published date if available
                                    # Icarus seems to use countdown_end as the release date
                                    published = victim.get('countdown_end', '')
                                    
                                    appender(
                                        victim=name,
                                        group_name='icarus',
                                        description=description,
                                        website="",
                                        published=published,
                                        post_url="",
                                        country=""
                                    )
                                continue # Skip fallback if script parsing worked
                            except json.JSONDecodeError:
                                pass
                    
                    # Fallback to HTML parsing if script not found or failed
                    divs_victim = soup.find_all('div', class_='victim-item')
                    for div in divs_victim:
                        name = div.get('data-name', '').strip()
                        description = div.get('data-desc', '').strip()
                        
                        appender(
                            victim=name,
                            group_name='icarus',
                            description=description,
                            website="",
                            published="",
                            post_url="",
                            country=""
                        )
        except Exception as e:
            errlog('icarus - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
