"""
    Upgraded API Parser for Termite
"""

import os
import json
import requests
import urllib3
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "termite"
api_endpoint_suffix = "api/blog/blogs"

# Disable the warning about certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic proxy settings
proxies = {
    'http': proxy_address.replace('socks5://', 'socks5h://'),
    'https': proxy_address.replace('socks5://', 'socks5h://')
}

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

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://termitelfvhutinrgpe55siktisskbqntkuq7ojidg42zh26avekq6qd.onion']

    # Initialize session for "browser etiquette"
    session = requests.Session()
    session.proxies = proxies
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })

    for base_url in base_urls:
        try:
            # 1. Visit top page to initialize session
            stdlog(f"[{target_group_name}] Visiting top page: {base_url}")
            session.get(base_url, verify=False, timeout=60)
            
            # 2. Fetch API
            full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
            stdlog(f"[{target_group_name}] Fetching API with session: {full_api_url}")
            
            headers = {"Referer": base_url + "/"}
            response = session.get(full_api_url, headers=headers, verify=False, timeout=120)
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                except Exception as json_err:
                    errlog(f"Termite API response was not JSON for {full_api_url}. Content type: {response.headers.get('Content-Type')}")
                    continue

                for victim in json_data:
                    title = victim.get('title', 'Unknown')
                    website = victim.get('address', '')
                    description = victim.get('description', '')
                    published = victim.get('publishDate', '')
                    try:
                        dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S.%fZ")
                        published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                    except: pass
                    
                    post_url = urljoin(base_url + '/', f"post/{victim.get('_id', '')}")
                    appender(title, target_group_name, description, website, published, post_url)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Termite API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
