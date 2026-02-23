"""
    Upgraded API Parser for Lynx
"""

import os
import json
import requests
import urllib3
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin, unquote
from datetime import datetime
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "lynx"
api_endpoint_suffix = "api/v1/blog/get/announcements"

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

def convert_datetime(ms_timestamp):
    try:
        dt = datetime.fromtimestamp(ms_timestamp / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    except:
        return ""

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://lynxblogxutufossaeawlij3j3uikaloll5ko6grzhkwdclrjngrfoid.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                json_data = response.json()
                announcements = json_data.get('payload', {}).get('announcements', [])
                for item in announcements:
                    victim = unquote(item.get('company', {}).get('company_name', 'Unknown'))
                    description = unquote(item.get('description', [''])[0])
                    published = convert_datetime(item.get('createdAt', 0))
                    post_url = urljoin(base_url + '/', f"leaks/{item.get('_id', '')}")
                    
                    appender(victim, target_group_name, description, "", published, post_url)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Lynx API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
