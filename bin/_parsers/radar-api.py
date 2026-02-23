"""
    Upgraded API Parser for Radar
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

target_group_name = "radar"
api_endpoints = ["api/leakeds_a", "api/leakeds_u"]

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

def clean_text(t):
    if not t: return ""
    t = html.unescape(t)
    t = re.sub(r"\r\n?", "\n", t)
    return t.strip()

def normalize_published(created_at):
    if not created_at: return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            dt = datetime.strptime(created_at, fmt).replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        except: continue
    return created_at

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['http://3bnusfu2lgk5at43ceu7cdok5yv4gfbono2jv57ho74ucjvc7czirfid.onion']

    for base_url in base_urls:
        success = False
        for endpoint in api_endpoints:
            full_api_url = urljoin(base_url + '/', endpoint)
            stdlog(f"Fetching {target_group_name} API: {full_api_url}")
            
            try:
                response = requests.get(full_api_url, proxies=proxies, verify=False, timeout=45)
                if response.status_code == 200:
                    records = response.json()
                    if records:
                        for entry in records:
                            victim = (entry.get("company_name") or "").strip()
                            desc = clean_text(entry.get("description") or entry.get("blog") or "")
                            website_raw = (entry.get("website") or "").strip()
                            website_fqdn = urlparse(website_raw).netloc.lower() if website_raw.startswith("http") else ""
                            published = normalize_published(entry.get("created_at") or "")
                            appender(victim, target_group_name, desc, website_fqdn, published)
                        success = True
            except Exception as e:
                errlog(f"Radar API Error for {full_api_url}: {e}")
        if success: return

if __name__ == "__main__":
    main()
