"""
    Upgraded API/HTML Parser for World Leaks
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
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
tmp_dir = home / os.getenv("TMP_DIR", "tmp").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "worldleaks"
api_endpoint_suffix = "/api/companies"

# Disable the warning about certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic proxy settings
proxies = {
    'http': proxy_address.replace('socks5://', 'socks5h://'),
    'https': proxy_address.replace('socks5://', 'socks5h://')
}

def convert_date(unix_timestamp):
    try:
        ts = int(unix_timestamp)
        if ts > 10**11: ts /= 1000  # Convert ms to s
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return ""

def get_base_urls():
    try:
        groups_file = db_dir / "groups.json"
        if not groups_file.exists():
            return []
        with open(groups_file, 'r', encoding='utf-8') as file:
            groups_data = json.load(file)
        group = next((g for g in groups_data if g.get('name') == target_group_name), None)
        if group and group.get('locations'):
            return [loc.get('slug').rstrip('/') for loc in group['locations'] if loc.get('enabled', True)]
    except Exception as e:
        errlog(f"Error reading groups.json: {e}")
    return []

def parse_api():
    base_urls = get_base_urls()
    if not base_urls:
        base_urls = ['http://worldleaksartrjm3c6vasllvgacbi5u3mgzkluehrzhk2jz4taufuid.onion']

    success = False
    # Use a session to maintain cookies/headers across requests
    session = requests.Session()
    session.proxies = proxies
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })

    for base_url in base_urls:
        full_api_url = base_url + api_endpoint_suffix
        try:
            # 1. "Greeting" - Visit the top page first to initialize session/cookies
            stdlog(f"[{target_group_name}] Visiting top page to initialize session: {base_url}")
            session.get(base_url, verify=False, timeout=30)
            
            # 2. Access the API with Referer header
            stdlog(f"[{target_group_name}] Fetching API with session: {full_api_url}")
            
            headers = {"Referer": base_url + "/"}
            response = session.get(full_api_url, headers=headers, verify=False, timeout=120)
            
            if response.status_code == 200:
                content = response.text.strip()
                # Handle both a single JSON array/object and JSONL (one JSON per line)
                items = []
                try:
                    data = json.loads(content)
                    items = data if isinstance(data, list) else data.get('data', [])
                except json.JSONDecodeError:
                    # Try parsing line by line (JSONL)
                    for line in content.splitlines():
                        if line.strip():
                            try:
                                items.append(json.loads(line.strip()))
                            except:
                                continue
                
                if not items:
                    stdlog(f"[{target_group_name}] No data found in API response from {base_url}")
                    continue

                for item in items:
                    # Robust field extraction with null handling
                    title = item.get('title')
                    if title is None:
                        title = ""
                    title = str(title).strip()
                    
                    if not title: continue
                    
                    post_id = item.get('id', '')
                    website = item.get('website')
                    if website is None:
                        website = ""
                    website = str(website).strip().replace("https:// http", "http")
                    
                    published = convert_date(item.get('updated_at', 0))
                    country_code = str(item.get('country', '') or '').upper()
                    post_url = f"{base_url}/companies/{post_id}"

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
            else:
                errlog(f"[{target_group_name}] API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"[{target_group_name}] API Request failed for {full_api_url}: {str(e).splitlines()[0]}")
    return success

def parse_files():
    stdlog(f"[{target_group_name}] Falling back to local file parsing")
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(target_group_name + '-'):
            continue
            
        file_path = tmp_dir / filename
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content or len(content) < 50:
                continue

            # Try JSON-per-line (old format)
            json_success = False
            for line in content.strip().splitlines():
                try:
                    item = json.loads(line.strip())
                    if isinstance(item, dict) and 'title' in item:
                        appender(
                            victim=item.get('title', '').strip(),
                            group_name=target_group_name,
                            description=item.get('description', ''),
                            website=item.get('website', '').strip(),
                            published=convert_date(item.get('updated_at', 0)),
                            post_url=f"https://worldleaksartrjm3c6vasllvgacbi5u3mgzkluehrzhk2jz4taufuid.onion/companies/{item.get('id', '')}",
                            country=item.get('country', '').upper()
                        )
                        json_success = True
                except:
                    continue
            
            if json_success:
                continue

            # Try HTML parsing (BeautifulSoup)
            soup = BeautifulSoup(content, 'html.parser')
            # Look for Angular components
            items = soup.find_all('app-company-list-item')
            for item in items:
                try:
                    # Title is in div.title -> div.content
                    title_el = item.find('div', class_='content')
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    
                    # Link is in the parent <a> tag
                    parent_a = item.find_parent('a', href=True)
                    post_url = ""
                    if parent_a:
                        post_url = urljoin('http://worldleaksartrjm3c6vasllvgacbi5u3mgzkluehrzhk2jz4taufuid.onion/', parent_a['href'])
                    
                    # Other info
                    description = ""
                    meta_items = item.find_all('div', class_='item')
                    for meta in meta_items:
                        m_title = meta.find('div', class_='title')
                        m_value = meta.find('div', class_='value')
                        if m_title and m_value:
                            description += f"{m_title.get_text(strip=True)}: {m_value.get_text(strip=True)}; "
                    
                    # Country
                    country = ""
                    country_el = item.find('div', class_='country')
                    if country_el:
                        country = country_el.get_text(strip=True)

                    if title:
                        appender(victim=title, group_name=target_group_name, description=description, post_url=post_url, country=country)
                except Exception as e:
                    errlog(f"[{target_group_name}] Error parsing item in {filename}: {e}")

        except Exception as e:
            errlog(f"[{target_group_name}] Error processing file {filename}: {e}")

def main():
    # 1. Try API first
    api_success = parse_api()
    
    # 2. Fallback to file parsing (always run to catch anything missed)
    parse_files()

if __name__ == "__main__":
    main()
