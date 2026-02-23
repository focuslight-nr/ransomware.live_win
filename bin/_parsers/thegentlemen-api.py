"""
    Upgraded API Parser for TheGentlemen
"""

import os
import json
import requests
import urllib3
import re
import html
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "the gentlemen"
api_endpoint_suffix = "api/companies"

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

def sec_to_utc_str(sec_val):
    try:
        dt = datetime.fromtimestamp(int(sec_val), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

def clean_desc(text):
    if not text: return ""
    t = html.unescape(text)
    t = re.sub(r"\r\n?", "\n", t)
    return t.strip()

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://tezwsse5czllksjb7cwp65rvnk4oobmzti2znn42i43bjdfd2prqqkad.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                records = response.json()
                for entry in records:
                    title = (entry.get("title") or "").strip()
                    desc_raw = entry.get("description") or ""
                    timer_start = entry.get("timerStart") or 0
                    published = sec_to_utc_str(timer_start)
                    description = clean_desc(desc_raw)
                    
                    appender(title, target_group_name, description, "", published, base_url)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"TheGentlemen API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
