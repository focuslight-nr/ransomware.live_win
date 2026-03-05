"""
    Parser for LAPSUS$ group
    Extracts victims from the 'target-card' div classes.
"""

import os
from bs4 import BeautifulSoup
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
home = Path(__file__).resolve().parent.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

tmp_dir = home / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('lapsus$group-') and filename.endswith('.html'):
            file_path = tmp_dir / filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                
                md5_hash = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5('lapsus$ group', md5_hash) or ""
                
                # Each victim is in a target-card
                cards = soup.find_all('div', class_='target-card')
                for card in cards:
                    name_span = card.find('span', class_='target-name')
                    if name_span:
                        # Extract text and clean up (remove icon text if any, though .get_text() usually handles it)
                        victim_name = name_span.get_text(strip=True)
                        
                        # Sometimes there's a status/format next to it in another span
                        description = ""
                        header = card.find('div', class_='target-header')
                        if header:
                            status_span = header.find_all('span')
                            if len(status_span) > 1:
                                description = status_span[1].get_text(strip=True)
                        
                        # Links are in mirror-list
                        post_url = ""
                        mirror_list = card.find('div', class_='mirror-list')
                        if mirror_list:
                            # Prefer the first link that isn't a '#' or just an icon
                            links = mirror_list.find_all('a', href=True)
                            for link in links:
                                if link['href'] != '#' and not link['href'].startswith('javascript:'):
                                    post_url = link['href']
                                    break
                        
                        if victim_name:
                            appender(victim_name, 'lapsus$ group', description, "", "", post_url)
                
            except Exception as e:
                errlog(f"LAPSUS$ - Parsing failed for {filename}: {e}")

if __name__ == "__main__":
    main()
