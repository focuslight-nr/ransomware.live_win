"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

"""
    Hybrid API/HTML Parser for Everest
    Inspired by Worldleaks logic to extract more detailed info (website, description, etc.)
"""

import os
import json
import requests
import urllib3
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urljoin
from shared_utils import appender, stdlog, errlog, find_slug_by_md5, extract_md5_from_filename

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
tmp_dir = home / os.getenv("TMP_DIR", "tmp").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "everest"
api_endpoint_suffix = "/api/companies"

# Disable the warning about certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic proxy settings
proxies = {
    'http': proxy_address.replace('socks5://', 'socks5h://'),
    'https': proxy_address.replace('socks5://', 'socks5h://')
}

def parse_api():
    try:
        groups_file = db_dir / "groups.json"
        if not groups_file.exists():
            return False
        with open(groups_file, 'r', encoding='utf-8') as file:
            groups_data = json.load(file)
        group = next((g for g in groups_data if g.get('name') == target_group_name), None)
        if not (group and group.get('locations')):
            return False
        base_urls = [loc.get('slug').rstrip('/') for loc in group['locations'] if loc.get('enabled', True)]
    except Exception as e:
        errlog(f"[{target_group_name}] Error reading groups.json: {e}")
        return False

    success = False
    session = requests.Session()
    session.proxies = proxies
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    })

    for base_url in base_urls:
        try:
            full_api_url = base_url + api_endpoint_suffix
            stdlog(f"[{target_group_name}] Trying API: {full_api_url}")
            
            # Initial visit to set cookies
            session.get(base_url, verify=False, timeout=60)
            
            headers = {"Referer": base_url + "/"}
            response = session.get(full_api_url, headers=headers, verify=False, timeout=120)
            
            if response.status_code == 200:
                content = response.text.strip()
                try:
                    data = json.loads(content)
                    items = data if isinstance(data, list) else data.get('data', [])
                    if not items: continue

                    for item in items:
                        title = str(item.get('title') or '').strip()
                        if not title: continue
                        
                        website = str(item.get('website') or '').strip()
                        published_val = item.get('updated_at', 0)
                        published = ""
                        try:
                            ts = int(published_val)
                            if ts > 10**11: ts /= 1000
                            published = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")
                        except:
                            pass
                        
                        country_code = str(item.get('country', '') or '').upper()
                        post_id = item.get('id', item.get('translit', ''))
                        post_url = f"{base_url}/news/{post_id}"

                        if "Total Patient Care LLC" not in title:
                            appender(
                                victim=title,
                                group_name=target_group_name,
                                description=item.get('description', '') or '',
                                website=website,
                                published=published,
                                post_url=post_url,
                                country=country_code
                            )
                    success = True
                    stdlog(f"[{target_group_name}] API parsing successful for {base_url}")
                except json.JSONDecodeError:
                    stdlog(f"[{target_group_name}] API response not JSON from {base_url}")
        except Exception as e:
            stdlog(f"[{target_group_name}] API check failed for {base_url}: {e}")
    return success

def parse_html():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(target_group_name + '-'):
                html_doc = tmp_dir / filename
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Use current group locations to reconstruct post URLs
                md5_val = extract_md5_from_filename(str(html_doc))
                base_url = find_slug_by_md5(target_group_name, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')
                
                for div in soup.find_all('div', class_='category-item js-open-chat'):
                    title_tag = div.find('div', class_='category-title')
                    if not title_tag: continue
                    title = title_tag.get_text(strip=True)
                    
                    website = ""
                    domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-z]{2,6})', title)
                    if domain_match:
                        website = domain_match.group(1).lower()

                    clean_title = title.split(' - ')[0].strip()

                    date_tag = div.find('div', class_='category-date')
                    published = ''
                    if date_tag:
                        date_str = date_tag.get_text(strip=True).lower()
                        if date_str == 'today':
                            published = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        else:
                            try:
                                published_dt = datetime.strptime(date_str, '%d %b %Y')
                                published = published_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass
                    
                    translit = div.get('data-translit')
                    url = f"{base_url}/news/{translit}" if base_url else ""
   
                    if "Total Patient Care LLC" not in title:
                        appender(clean_title, target_group_name, '', website, published, url)
        except Exception as e:
            errlog(f"[{target_group_name}] HTML processing failed for {filename}: {e}")

def main():
    # 1. Try API first
    api_success = parse_api()
    
    # 2. Run HTML parsing (as fallback or addition)
    parse_html()

if __name__ == "__main__":
    main()


