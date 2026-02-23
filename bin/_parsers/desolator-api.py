"""
    Upgraded API Parser for Desolator
"""

import os
import json
import requests
import urllib3
import re
import pycountry
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

target_group_name = "desolator"
api_endpoint_suffix = "api/victims?page=1&rowsPerPage=50"

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
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return date_str

def clean_victim_name(display_name):
    if not display_name:
        return ""
    return re.sub(r"\s*\([^)]*\)\s*$", "", display_name).strip()

def extract_country_code(display_name):
    if not display_name:
        return ""
    match = re.search(r"\(([^)]+)\)\s*$", display_name)
    if not match:
        return ""
    country_name = match.group(1).strip()
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except:
        return country_name

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://po4tq2brx4rgwbdx4mac24fz34uuuf7oigosebp32n2462m2vxl6biqd.onion']

    for base_url in base_urls:
        full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
        stdlog(f"Fetching {target_group_name} API: {full_api_url}")
        
        try:
            response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
            if response.status_code == 200:
                data = response.json()
                victims = data.get("victims", [])
                for entry in victims:
                    victim = entry.get("display_name") or ""
                    description = f"Status: {entry.get('status','')} | Expiration: {entry.get('expiration_date','')}"
                    post_url = urljoin(base_url + '/', f"victim/{entry.get('victim_id')}")
                    published = convert_date(entry.get("infection_date"))
                    country = extract_country_code(entry.get("display_name"))
                    
                    appender(clean_victim_name(victim), target_group_name, description, "", published, post_url, country)
                return
            else:
                errlog(f"API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"Desolator API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
