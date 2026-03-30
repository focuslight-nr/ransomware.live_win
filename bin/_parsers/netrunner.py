"""
    Parser for NetRunner
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

target_group_name = "netrunner"
# Base URL from db/groups.json
base_url = "http://netrunrsb3bivj5gnwajzxlig5qkteb6edgthxj7fmsvhkzxtwfxwaad.onion"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('netrunner-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Each victim is in a 'blog-item' div
                items = soup.find_all('div', class_='blog-item')
                for item in items:
                    try:
                        # Extract Victim Name
                        title_tag = item.find('div', class_='blog-item-title')
                        if not title_tag:
                            continue
                        victim = title_tag.text.strip()
                        
                        # Extract Description
                        desc_tag = item.find('div', class_='blog-item-description')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        # Extract Website
                        website_tag = item.find('div', class_='blog-item-info-website')
                        website = ""
                        if website_tag:
                            website_links = website_tag.find_all('a')
                            if website_links:
                                # Take the first website link
                                website = website_links[0].text.strip()
                        
                        # Extract Location (Country)
                        location_tag = item.find('div', class_='blog-item-info-location')
                        if location_tag:
                            location_text = location_tag.get_text(separator=" ", strip=True).replace('Location:', '').strip()
                            if location_text:
                                if description:
                                    description = f"Location: {location_text}\n\n{description}"
                                else:
                                    description = f"Location: {location_text}"
                        
                        # Extract Post URL (Detail link)
                        button_tag = item.find('div', class_='blog-item-button')
                        post_url = ""
                        if button_tag:
                            link_tag = button_tag.find('a', href=True)
                            if link_tag:
                                post_url = urljoin(base_url, link_tag['href'])
                        
                        appender(victim, target_group_name, description, website, "", post_url)
                    except Exception as e:
                        errlog(f'{target_group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
