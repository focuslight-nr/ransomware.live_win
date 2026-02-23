"""
    Upgraded API Parser for Embargo
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

target_group_name = "embargo"
api_endpoint_suffix = "api/blog/get"

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

def convert_datetime(iso_datetime):
    try:
        if '+' in iso_datetime:
            return iso_datetime.split('+')[0].replace('T', ' ')
        dt_obj = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return iso_datetime.replace('T', ' ')

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://v7f6v7v7v7v7v7v7.onion'] # Placeholder if empty

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                json_data = response.json()
                blogs = json_data.get("blogs", [])
                for item in blogs:
                    title = item.get('comname', '').strip()
                    description = f"{item.get('descr', '')} - {item.get('comments', '')}"
                    published = convert_datetime(item.get('date_created', ''))
                    post_url = urljoin(base_url + '/', f"#/post/{item.get('_id', '')}")
                    
                    appender(title, target_group_name, description, "", published, post_url)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Embargo API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
