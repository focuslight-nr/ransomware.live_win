"""
    Parser for Morpheus (HTML Version)
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
    target_group = "morpheus"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f"{target_group}-"):
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

                # Posts are usually in div.post
                posts = soup.find_all('div', class_='post')
                for post in posts:
                    try:
                        description_parts = []
                        # Look for content within specific VKUI classes or fallback
                        content_div = post.find('div', class_='post__header')
                        if not content_div:
                            content_div = post

                        p_tags = post.find_all('p')
                        for p in p_tags:
                            p_text = p.get_text(strip=True)
                            if p_text:
                                description_parts.append(p_text)
                        
                        description = " ".join(description_parts)
                        
                        victim = ""
                        if description_parts:
                            first_p = description_parts[0]
                            match = re.match(r'^([^.]+?)\s+is\s+a\s+', first_p, re.I)
                            if match:
                                victim = match.group(1)
                            else:
                                victim = first_p[:100].split('\n')[0]

                        website = ""
                        domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-z]{2,6})', description)
                        if domain_match:
                            website = domain_match.group(1).lower()

                        published = ""
                        date_cell = post.find('div', class_='post__header__date')
                        if date_cell:
                            date_str = date_cell.get_text(strip=True)
                            try:
                                dt = datetime.strptime(date_str, "%d %B %Y")
                                published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str

                        post_url = ""
                        link_a = post.find('a', href=re.compile(r'/files/'))
                        if link_a and base_url:
                            post_url = urljoin(base_url, link_a['href'])

                        if victim:
                            appender(victim, target_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing post: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

