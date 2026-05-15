"""
    MedusaLocker Parser
    Extracts victim data from MedusaLocker ransomware group pages.
    Updated for new card-based structure.
"""

import os, datetime, sys, re
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
            if filename.startswith('medusalocker-') and filename.endswith('.html'):
                html_doc = tmp_dir / filename
                
                # Try to get base URL for full post links
                md5 = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5('medusa locker', md5)
                if not base_url:
                    base_url = ""
                base_url = base_url.rstrip('/')

                content = ""
                try:
                    with open(html_doc, "r", encoding="utf-8") as file:
                        content = file.read()
                except UnicodeDecodeError:
                    with open(html_doc, "r", encoding="latin-1") as file:
                        content = file.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # New card-based structure
                cards = soup.find_all('a', class_='card')
                if cards:
                    for card in cards:
                        name_el = card.find('div', class_='card-name')
                        if not name_el:
                            continue
                        name = name_el.text.strip()
                        
                        desc_el = card.find('div', class_='card-desc')
                        description = desc_el.text.strip() if desc_el else ""
                        
                        address_el = card.find('div', class_='card-address')
                        address = address_el.text.strip() if address_el else ""
                        if address:
                            description = f"Address: {address}\n\n{description}"
                        
                        # Extract published date from deadline if available
                        published = ""
                        timer_el = card.find('div', class_='card-timer')
                        if timer_el and timer_el.has_attr('data-deadline'):
                            deadline = timer_el['data-deadline']
                            try:
                                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM
                                if 'T' in deadline:
                                    published = datetime.strptime(deadline, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S.%f")
                                else:
                                    published = datetime.strptime(deadline, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass
                        
                        link = card.get('href', '')
                        if link.startswith('/') and base_url:
                            link = base_url + link
                        
                        appender(
                            victim=name,
                            group_name='medusa locker',
                            description=description,
                            website="",
                            published=published,
                            post_url=link,
                            country=""
                        )
                    continue # Skip old structure parsing if cards found

                # Old structure fallback (from existing parser)
                articles = soup.find_all('article')
                for article in articles:
                        link_el = article.find('a')
                        link = link_el['href'] if link_el else ""
                        
                        title_el = article.find('h2', class_='entry-title')
                        title = title_el.text.strip() if title_el else ""
                        
                        content_el = article.find('div', class_='entry-content')
                        content = content_el.text.strip() if content_el else ""
                        
                        date_element = article.find('time', class_='entry-date')
                        formatted_date = ""
                        if date_element and date_element.has_attr('datetime'):
                            published_date = date_element['datetime']
                            try:
                                formatted_date = datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass
                        
                        appender(title, 'medusa locker', content, '', formatted_date, link)
        except Exception as e:
            errlog('medusa locker - parsing fail with error: ' + str(e) + ' in file: ' + filename)

if __name__ == "__main__":
    main()
