import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "m3rx"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8', errors='ignore') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL for links
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                # Generic victim card search
                # Many groups use 'card', 'post', or 'item'
                items = soup.find_all('div', class_=re.compile(r'card|post|item', re.I))
                
                if not items:
                    # Try a different approach if no items found with classes
                    # Look for containers that have a heading
                    items = soup.find_all(['div', 'article', 'section'])

                for item in items:
                    try:
                        # Search for a title in headings
                        title_tag = item.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                        if not title_tag:
                            # Try to find a strong tag or a div with title in class
                            title_tag = item.find(['strong', 'b']) or item.find('div', class_=re.compile(r'title', re.I))
                        
                        if not title_tag:
                            continue

                        title = title_tag.get_text(strip=True)
                        # Filter out common non-victim titles
                        if len(title) < 2 or title.lower() in ['menu', 'navigation', 'home', 'faq', 'contact', 'about', 'rules', 'news']:
                            continue

                        # Website search
                        website = ""
                        web_tag = item.find('a', href=re.compile(r'^http'))
                        if web_tag:
                            website = web_tag['href']
                        
                        # If title looks like a domain, use it as website
                        if not website and '.' in title and ' ' not in title:
                            website = title

                        # Description
                        description = ""
                        desc_tag = item.find(['p', 'div'], class_=re.compile(r'desc|text|content|body', re.I))
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)
                        else:
                            # Use siblings or paragraphs within the item
                            paragraphs = item.find_all('p')
                            if paragraphs:
                                description = " ".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True) != title])
                            else:
                                # Last resort: use all text in the item excluding the title
                                full_text = item.get_text(separator=' ', strip=True)
                                description = full_text.replace(title, '', 1).strip()

                        # Published date
                        published = ""
                        # Look for common date patterns or tags
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', item.get_text())
                        if date_match:
                            published = date_match.group(0)

                        # Link
                        link = base_url
                        a_tags = item.find_all('a')
                        for a in a_tags:
                            if a.has_attr('href') and not a['href'].startswith('http'):
                                link = os.path.join(base_url, a['href'].lstrip('/'))
                                break
                            elif a.has_attr('href') and '.onion' in a['href']:
                                link = a['href']
                                break

                        appender(title, group_name, description, website, published, link)
                    except Exception as e:
                        # Skip items that fail to parse
                        continue
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
