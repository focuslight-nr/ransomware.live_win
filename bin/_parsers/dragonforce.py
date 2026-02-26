"""
    Parser for Dragon Force (HTML Version)
"""

import os
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
        if filename.startswith("dragon force-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                items = soup.find_all('div', class_='publications-list__publication')
                for item in items:
                    try:
                        name_tag = item.find('h3', class_='list-publication__name')
                        if not name_tag:
                            continue
                        victim = name_tag.get_text(strip=True)

                        website = ""
                        ws_tag = item.find('p', class_='list-publication__website')
                        if ws_tag:
                            website = ws_tag.get_text(strip=True)
                        else:
                            ws_a = item.find('a', class_='addictional-row__link')
                            if ws_a:
                                website = ws_a.get_text(strip=True)

                        description = ""
                        desc_div = item.find('div', class_='publication-top')
                        if desc_div:
                            # Try to find all paragraphs and combine, excluding website
                            p_tags = desc_div.find_all('p')
                            desc_parts = []
                            for p in p_tags:
                                p_text = p.get_text(strip=True)
                                if p_text and p_text != website:
                                    desc_parts.append(p_text)
                            description = " ".join(desc_parts)

                        published = ""
                        date_tag = item.find('span', class_='publication-footer__date')
                        if date_tag:
                            published_str = date_tag.get_text(strip=True)
                            # Remove icon if any (creation mdi)
                            published_str = re.sub(r'\s+', ' ', published_str).strip()
                            try:
                                # Format: "18 February 2026"
                                dt = datetime.strptime(published_str, "%d %B %Y")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = published_str

                        appender(victim, target_group, description, website, published)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

