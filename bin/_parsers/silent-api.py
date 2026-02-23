"""
    Upgraded API Parser for Silent
"""

import os
import json
import requests
import urllib3
import tldextract
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

target_group_name = "silent"
api_endpoints = ["api/company/", "api/disclosures/"]

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

def country_to_code(name):
    try:
        country = pycountry.countries.get(name=name)
        return country.alpha_2 if country else ""
    except: return ""

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://silentbgdghp3zeldwpumnwabglreql7jcffhx5vqkvtf2lshc4n5zid.onion']

    for base_url in base_urls:
        # Companies
        try:
            url = urljoin(base_url + '/', api_endpoints[0])
            stdlog(f"Fetching {target_group_name} Companies: {url}")
            resp = requests.get(url, proxies=proxies, verify=False, timeout=45)
            if resp.status_code == 200:
                json_data = resp.json()
                for company in json_data.get("companies", []):
                    name = company.get("company_name", "").strip()
                    country = company.get("country", "")
                    revenue = company.get("revenue", "")
                    employees = company.get("employees", "")
                    tags = ", ".join([t['name'] for t in company.get("tag_names", [])])
                    description = f"Country: {country} | Revenue: {revenue}M USD | Employees: {employees} | Tags: {tags}"
                    
                    link = company.get("link", "")
                    domain = f"{tldextract.extract(link).domain}.{tldextract.extract(link).suffix}" if link else ""
                    appender(name, target_group_name, description, domain, "", base_url, country_to_code(country))
        except Exception as e:
            errlog(f"Silent Company API Error for {base_url}: {e}")

        # Disclosures
        try:
            url = urljoin(base_url + '/', api_endpoints[1])
            stdlog(f"Fetching {target_group_name} Disclosures: {url}")
            resp = requests.get(url, proxies=proxies, verify=False, timeout=45)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for disc in results:
                    name = disc.get("company_name", "")
                    description = disc.get("description") or "Not claimed yet"
                    extra = { 'data_size': disc.get("filesSizes", "") }
                    appender(name, target_group_name, description, "", "", base_url, "", extra)
        except Exception as e:
            errlog(f"Silent Disclosure API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
