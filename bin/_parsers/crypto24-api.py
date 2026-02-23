"""
    Upgraded API Parser for Crypto24
"""

import os
import json
import requests
import urllib3
import pycountry
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

target_group_name = "crypto24"
api_endpoint_suffix = "api/data?page=1"

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

def convert_country_to_code(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except:
        return ""

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://j5o5y2feotmhvr7cbcp2j2ewayv5mn5zenl3joqwx67gtfchhezjznad.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        headers = {
            "Host": base_url.split('//')[-1].split(':')[0],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": base_url + '/'
        }

        try:
            response = requests.get(full_api_url, headers=headers, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                json_data = response.json()
                if "items" in json_data:
                    for item in json_data["items"]:
                        company = item.get('company', '').strip()
                        domain = item.get('domain', '').strip()
                        comment = item.get('comment', '').strip()
                        country = item.get('country', '').strip()
                        published = item.get('time', '')[:10]
                        country_code = convert_country_to_code(country) if country else item.get('code', '')
                        extra_infos = { 'size': item.get('size', '') }
                        
                        appender(company, target_group_name, comment, domain, published, '', country_code, extra_infos)
                    return # Success
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Request failed for {full_api_url}: {e}")

if __name__ == "__main__":
    main()
