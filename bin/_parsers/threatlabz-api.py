"""
    API Parser for ThreatLabz
"""

import os
import json
import requests
import urllib3
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urljoin
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "threatlabz"
api_endpoint_suffix = "news.php?allNewsPage=1"

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
            urls = [loc.get('slug').rstrip('/') for loc in group['locations'] if loc.get('enabled', True)]
            if urls: return urls
    except Exception as e:
        errlog(f"Error reading groups.json: {e}")
    
    # Fallback
    return ['http://blogvl7tjyjvsfthobttze52w36wwiz34hrfcmorgvdzb6hikucb7aqd.onion']

def main():
    base_urls = get_base_urls()
    
    session = requests.Session()
    session.proxies = proxies
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    for base_url in base_urls:
        try:
            # 1. Visit root to init session
            stdlog(f"[{target_group_name}] Visiting top page: {base_url}")
            session.get(base_url, verify=False, timeout=60)
            
            # 2. Fetch API
            full_api_url = urljoin(base_url + '/', api_endpoint_suffix)
            stdlog(f"[{target_group_name}] Fetching API: {full_api_url}")
            
            response = session.get(full_api_url, verify=False, timeout=120)
            if response.status_code == 200:
                summary_data = response.json()
                stdlog(f"[{target_group_name}] Found {len(summary_data)} entries in summary")
                
                for summary_item in summary_data:
                    victim_name = summary_item.get('name', '').strip()
                    page_id = summary_item.get('pageId')
                    if not victim_name or page_id is None: continue
                    
                    # Normalize date
                    raw_date = summary_item.get('createdDate') or summary_item.get('updatedDate', '')
                    published = raw_date.replace('.', '-')
                    
                    # Fetch details for this specific victim
                    detail_url = urljoin(base_url + '/', f"news.php?contentId={page_id}")
                    description = ""
                    website = ""
                    post_url = base_url # Default
                    
                    try:
                        detail_resp = session.get(detail_url, verify=False, timeout=60)
                        if detail_resp.status_code == 200:
                            details = detail_resp.json()
                            # Find the detail block that has a 'description'
                            for d in details:
                                d_obj = d.get('data', {})
                                if d_obj.get('description'):
                                    description = d_obj['description'].strip()
                                    # Try to extract website from description if not found
                                    web_match = re.search(r'Website:\s*([\w.-]+\.[a-zA-Z]{2,})', description, re.I)
                                    if web_match:
                                        website = web_match.group(1)
                                    break
                    except Exception as e:
                        stdlog(f"[{target_group_name}] Failed to fetch details for ID {page_id}: {str(e).splitlines()[0]}")

                    appender(
                        victim=victim_name,
                        group_name=target_group_name,
                        description=description,
                        website=website,
                        published=published,
                        post_url=post_url
                    )
                return
            else:
                errlog(f"[{target_group_name}] API Error ({response.status_code}) for {full_api_url}")
        except Exception as e:
            errlog(f"[{target_group_name}] Request failed for {base_url}: {str(e).splitlines()[0] if str(e).splitlines() else str(e)}")

if __name__ == "__main__":
    main()
