"""
    Upgraded API Parser for Cephalus
"""

import os
import json
import requests
import urllib3
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime, timezone
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "cephalus"
api_endpoint_suffix = "/api/domains"

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
        base_urls = ['http://cephalus6oiypuwumqlwurvbmwsfglg424zjdmywfgqm4iehkqivsjyd.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix.lstrip('/'))
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    victim = entry.get("company") or entry.get("domain")
                    description = entry.get("description") or ""
                    website = entry.get("domain") or ""
                    post_url = entry.get("dataLink") or ""
                    
                    appender(victim, target_group_name, description, website, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), post_url)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Cephalus API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
