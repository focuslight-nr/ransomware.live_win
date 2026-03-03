import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "mydata_alphalocker"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL for links
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                # The news blog section contains victim info
                news_blog = soup.find('div', class_='news_blog')
                if not news_blog:
                    continue

                # Items are in div blocks with links
                # In this specific page, it's a bit messy, let's look for links that look like victim pages
                links = news_blog.find_all('a', href=re.compile(r'blog_'))
                
                processed_titles = set()

                for link_tag in links:
                    title = link_tag.get_text(strip=True)
                    if not title or title == "Read more" or title in processed_titles:
                        continue
                    
                    processed_titles.add(title)

                    # Description is usually the next sibling text or in the same div
                    description = ""
                    parent_div = link_tag.find_parent('div')
                    if parent_div:
                        description = parent_div.get_text(separator=' ', strip=True).replace(title, '').replace('Read more', '').strip()

                    website = ""
                    if title.startswith('http'):
                        website = title
                        title = title.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

                    post_url = urljoin(base_url, link_tag['href']) if base_url else link_tag['href']

                    appender(title, group_name, description, website, '', post_url)
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
