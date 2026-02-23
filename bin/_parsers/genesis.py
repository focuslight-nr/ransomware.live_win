"""
    Upgraded Parser for Genesis
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

target_group_name = "genesis"
base_url = "http://genesis6ixpb5mcy4kudybtw5op2wqlrkocfogbnenz3c647ibqixiad.onion"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith(target_group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Hugo PaperMod theme typical structure
                articles = soup.find_all('article', class_='post-entry')
                if not articles:
                    # Fallback to general article tag
                    articles = soup.find_all('article')
                
                for article in articles:
                    try:
                        header = article.find('header', class_='entry-header')
                        title_tag = header.find('h2') if header else article.find('h2')
                        if not title_tag:
                            continue
                        
                        victim = title_tag.text.strip()
                        
                        # Link
                        link_tag = article.find('a', class_='entry-link') or article.find('a', href=True)
                        post_url = urljoin(base_url, link_tag['href']) if link_tag else ""
                        
                        # Summary
                        summary_tag = article.find('div', class_='entry-content') or article.find('section')
                        description = summary_tag.text.strip() if summary_tag else ""
                        
                        # Date
                        footer = article.find('footer', class_='entry-footer')
                        published = ""
                        if footer:
                            time_tag = footer.find('time')
                            if time_tag and time_tag.get('datetime'):
                                published = time_tag['datetime']
                            else:
                                published = footer.text.strip()

                        appender(victim, target_group_name, description, "", published, post_url)
                    except Exception as e:
                        errlog(f'{target_group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
