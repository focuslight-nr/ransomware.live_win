"""
    Parser for BravoX
    Works best with rendered HTML (SPA)
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
import re
from datetime import datetime

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    target_group = "bravox"
    # Also look for the rendered test file for verification
    filenames = os.listdir(tmp_dir)
    
    for filename in filenames:
        if filename.startswith(f"{target_group}-") or filename == "bravox_rendered_test.html":
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')

                # Cards are in div.bg-card
                cards = soup.find_all('div', class_='bg-card')
                for card in cards:
                    try:
                        # Title
                        title_tag = card.find('h3', class_='text-xl')
                        if not title_tag:
                            continue
                        victim_raw = title_tag.get_text(strip=True)
                        # Extract country emoji if present
                        country_match = re.search(r'([\U0001f1e6-\U0001f1ff]{2})', victim_raw)
                        country = country_match.group(1) if country_match else ""
                        # Clean title
                        victim = re.sub(r'[\U0001f1e6-\U0001f1ff]{2}', '', victim_raw).strip()

                        # Website
                        website = ""
                        links = card.find_all('a', href=True)
                        for a in links:
                            href = a['href']
                            if href.startswith('http') and target_group not in href:
                                website = href
                                break

                        # Description
                        description = ""
                        desc_div = card.find('div', class_='flex-1')
                        if desc_div:
                            p_tag = desc_div.find('p')
                            description = p_tag.get_text(strip=True) if p_tag else desc_div.get_text(strip=True)

                        # Date
                        published = ""
                        date_span = card.find('span', class_='text-muted-foreground')
                        if date_span:
                            date_str = date_span.get_text(strip=True)
                            # Handle relative dates like "~13h ago"
                            if 'ago' in date_str:
                                published = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                            else:
                                try:
                                    # Format: "18/02/2026 02:48"
                                    dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = date_str

                        # post_url
                        post_url = ""
                        blog_link = card.find('a', href=re.compile(r'/blog/'))
                        if blog_link:
                            post_url = urljoin(base_url, blog_link['href']) if base_url else blog_link['href']

                        if victim and "On pre-release step" not in victim:
                            appender(victim, target_group, description, website, published, post_url, country)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing card: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

