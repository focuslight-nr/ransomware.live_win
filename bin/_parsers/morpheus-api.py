"""
    Upgraded API Parser for Morpheus
"""

import os
import json
import requests
import urllib3
import re
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
from datetime import datetime
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "morpheus"
api_endpoint_suffix = "intrumpwetrust/api/posts?page=1&perPage=50"

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

def extract_website(text):
    match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text)
    if match:
        url = match.group(0)
        if url.startswith("www."): url = "http://" + url
        return urlparse(url).netloc
    return ""

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://izsp6ipui4ctgxfugbgtu65kzefrucltyfpbxplmfybl5swiadpljmyd.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    victim = item.get('title', 'Unknown')
                    text = item.get('text', '')
                    published = item.get('date', '')
                    try:
                        published = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S.%f")
                    except: pass
                    
                    description = text[:300] if text else ""
                    website = extract_website(text) if text else ""
                    
                    appender(victim, target_group_name, description, website, published)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Morpheus API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
