"""
    Upgraded API Parser for CrazyHunter
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

target_group_name = "crazy hunter team"
# CrazyHunter uses port 8088 for API
api_endpoint_suffix = ":8088/api/v1/product?page=1&pageSize=50"

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

def convert_timestamp(iso_timestamp):
    try:
        dt = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return iso_timestamp

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://7i6sfmfvmqfaabjksckwrttu3nsbopl3xev2vbxbkghsivs5lqp4yeqd.onion']

    for base_url in base_urls:
        full_api_url = base_url + api_endpoint_suffix
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and "list" in data.get("data", {}):
                    products = data["data"]["list"]
                    for product in products:
                        name = product.get('productName', 'Unknown')
                        victim = name.split("-", 1)[-1].strip() if "-" in name else name
                        description = product.get('productDesc', '')
                        published = convert_timestamp(product.get('CreatedAt', ''))
                        post_url = f"{base_url}/product/{product.get('ID', '')}"
                        extra_infos = { 'ransom': product.get('productPrice', '') }
                        
                        appender(victim, target_group_name, description, '', published, post_url, '', extra_infos)
                    return # Success
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Request failed for {full_api_url}: {e}")

if __name__ == "__main__":
    main()
