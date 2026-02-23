"""
    Upgraded API Parser for BlackNevas
"""

import os
import json
import requests
import urllib3
import re
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

target_group_name = "blacknevas"

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

def format_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return dt_str

def extract_company_and_website(company_field):
    website = ""
    name = company_field
    m = re.match(r"^(.*?)(?:\s+(https?://|www\.)[^\s]+)?$", company_field.strip())
    if m:
        name = m.group(1).strip()
        url_match = re.search(r"(https?://[^\s]+|www\.[^\s]+)", company_field)
        if url_match:
            website = url_match.group(1)
    return name, website

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://ctyfftrjgtwdjzlgqh4avbd35sqrs6tde4oyam2ufbjch6oqpqtkdtid.onion']

    for base_url in base_urls:
        try:
            # Fetch Category Mapping
            cat_url = urljoin(base_url + '/', 'api/category')
            stdlog(f"Fetching {target_group_name} Categories: {cat_url}")
            cat_resp = requests.get(cat_url, proxies=proxies, verify=False, timeout=30)
            cat_map = {cat['id']: cat['name'] for cat in cat_resp.json()} if cat_resp.status_code == 200 else {}

            # Fetch Victims
            api_url = urljoin(base_url + '/', 'api/publication')
            stdlog(f"Fetching {target_group_name} Victims: {api_url}")
            resp = requests.get(api_url, proxies=proxies, verify=False, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    company_name, website = extract_company_and_website(item.get("company", ""))
                    created_at = item.get("createdAt", "")[:19].replace("T", " ")
                    desc_html = item.get("description", "")
                    desc_text = re.sub('<[^<]+?>', '', desc_html).strip()
                    category_name = cat_map.get(item.get('categoryId'), "Unknown")
                    post_url = urljoin(base_url + '/', f"publications/details/{item.get('id')}")
                    extra_infos = { 'Activity': category_name, 'Revenue': item.get('revenue') }
                    
                    appender(company_name, target_group_name, desc_text, website, format_datetime(created_at), post_url, "", extra_infos)
                return
        except Exception as e:
            errlog(f"BlackNevas API Error for {base_url}: {e}")

if __name__ == "__main__":
    main()
