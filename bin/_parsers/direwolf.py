"""
    Parser for Dire Wolf
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
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
    target_group = "direwolf"
    for filename in os.listdir(tmp_dir):
        if filename.startswith("dire wolf-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL to reconstruct links if possible
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                cards = soup.find_all('div', class_='card')
                for card in cards:
                    try:
                        title_tag = card.find('h2', class_='card-title')
                        if not title_tag:
                            continue
                        
                        # Extract victim name (excluding flag)
                        victim = title_tag.get_text(strip=True)
                        # Remove emoji flags if any
                        victim = re.sub(r'[^\x00-\x7F]+', '', victim).strip()
                        # If victim becomes empty after emoji removal, try keeping original but cleaned
                        if not victim:
                             victim = title_tag.get_text(strip=True)

                        meta_tag = card.find('div', class_='card-meta')
                        published = ""
                        if meta_tag:
                            published_str = meta_tag.text.replace('Published:', '').strip()
                            try:
                                # Assuming format YYYY-MM-DD
                                published_dt = datetime.strptime(published_str, '%Y-%m-%d')
                                published = published_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = published_str

                        website = ""
                        description_parts = []
                        summary_items = card.find_all('div', class_='card-summary-item')
                        for s_item in summary_items:
                            label = s_item.find('span', class_='card-summary-label')
                            value = s_item.find('span', class_='card-summary-value')
                            if label and value:
                                l_text = label.text.strip().lower()
                                v_text = value.text.strip()
                                if 'website' in l_text:
                                    website = v_text
                                else:
                                    description_parts.append(f"{label.text.strip()} {v_text}")
                        
                        description = " | ".join(description_parts)

                        # Handle post URL
                        link_tag = card.find('a', class_='card-link')
                        post_url = ""
                        if link_tag and link_tag.has_attr('onclick'):
                            # onclick="showArticleDetail(66)"
                            match = re.search(r'showArticleDetail\((\d+)\)', link_tag['onclick'])
                            if match and base_url:
                                article_id = match.group(1)
                                post_url = f"{base_url}/article/{article_id}"

                        appender(victim, target_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

