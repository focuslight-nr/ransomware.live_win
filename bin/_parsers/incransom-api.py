"""
    Upgraded API Parser for INC Ransom - New
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

# Group name as defined in groups.json
target_group_name = "inc ransom - new"
api_endpoint_suffix = "api/v1/blog/get/announcements?page=1&perPage=100"

# Disable the warning about certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic proxy settings
proxies = {
    'http': proxy_address.replace('socks5://', 'socks5h://'),
    'https': proxy_address.replace('socks5://', 'socks5h://')
}

def get_base_urls():
    urls = ['http://incbacg6bfwtrlzwdbqc55gsfl763s3twdtwhp27dzuik6s6rwdcityd.onion']
    try:
        groups_file = db_dir / "groups.json"
        if groups_file.exists():
            with open(groups_file, 'r', encoding='utf-8') as file:
                groups_data = json.load(file)
            group = next((g for g in groups_data if g.get('name') == target_group_name), None)
            if group and group.get('locations'):
                db_urls = [loc.get('slug').rstrip('/') for loc in group['locations'] if loc.get('enabled', True)]
                for u in db_urls:
                    if u not in urls:
                        urls.append(u)
    except Exception as e:
        errlog(f"Error reading groups.json: {e}")
    return urls

def main():
    base_urls = get_base_urls()
    
    # Initialize session for "browser etiquette"
    session = requests.Session()
    session.proxies = proxies
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    for base_url in base_urls:
        try:
            # 1. Visit top page to initialize session
            stdlog(f"[{target_group_name}] Visiting top page: {base_url}")
            session.get(base_url, verify=False, timeout=60)
            
            # 2. Fetch API
            full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
            stdlog(f"[{target_group_name}] Fetching API: {full_api_url}")
            
            response = session.get(full_api_url, verify=False, timeout=120)
            if response.status_code == 200:
                json_data = response.json()
                announcements = json_data.get('payload', {}).get('announcements', [])
                
                stdlog(f"[{target_group_name}] Found {len(announcements)} announcements")
                
                for ann in announcements:
                    company = ann.get('company', {})
                    company_name = unquote(company.get('company_name', 'Unknown')).strip()
                    if not company_name: continue
                    
                    # Flatten description list and unquote
                    desc_list = ann.get('description', [])
                    description = unquote(" ".join(desc_list)).strip()
                    
                    # Convert leakAt (ms) to string
                    published = ""
                    leak_at = ann.get('leakAt', 0)
                    if leak_at:
                        published = datetime.fromtimestamp(leak_at / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    post_id = ann.get('_id', '')
                    post_url = urljoin(base_url + '/', f"blog/disclosures/{post_id}")
                    country = unquote(company.get('country', '')).upper()
                    
                    appender(
                        victim=company_name,
                        group_name=target_group_name,
                        description=description,
                        published=published,
                        post_url=post_url,
                        country=country,
                        website=company_name # The name often contains the domain
                    )
                return # Stop after first successful location
            else:
                errlog(f"[{target_group_name}] API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"[{target_group_name}] Request failed for {base_url}: {str(e).splitlines()[0] if str(e).splitlines() else str(e)}")

if __name__ == "__main__":
    main()
