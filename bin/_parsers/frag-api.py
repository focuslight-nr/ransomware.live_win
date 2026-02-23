"""
    Upgraded API Parser for Frag
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

target_group_name = "frag"
api_endpoint_suffix = "tada/posts/leaks?page="

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

def convert_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return date_str

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://34o4m3f26ucyeddzpf53bksy76wd737nf2fytslovwd3viac3by5chad.onion']

    for base_url in base_urls:
        try:
            full_api_url = urljoin(base_url + '/', api_endpoint_suffix + "1")
            stdlog(f"Fetching {target_group_name} API (Page 1): {full_api_url}")
            
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                first_page = response.json()
                total_items = first_page.get("total", 0)
                per_page = first_page.get("perPage", 10)
                total_pages = (total_items + per_page - 1) // per_page if total_items else 1

                for page in range(1, min(total_pages + 1, 5)): # Limit to 5 pages for efficiency
                    page_url = urljoin(base_url + '/', api_endpoint_suffix + str(page))
                    page_data = requests.get(page_url, proxies=proxies, verify=False, timeout=30).json()
                    for item in page_data.get("items", []):
                        victim = item.get("title", "").split("|")[0].strip()
                        description = item.get("text", "")
                        published = convert_date(item.get("date", ""))
                        appender(victim, target_group_name, description, '', published)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Frag API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
