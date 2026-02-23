import os, sys, re
import urllib3
import requests
import json
from datetime import datetime
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME", ".")
db_dir = Path(home + os.getenv("DB_DIR", "/db/"))
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "bert"
api_endpoint = "/api/publications/s"

# Disable the warning about certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic proxy settings
proxies = {
    'http': proxy_address.replace('socks5://', 'socks5h://'),
    'https': proxy_address.replace('socks5://', 'socks5h://')
}

def get_base_url():
    try:
        with open(db_dir / "groups.json", 'r', encoding='utf-8') as file:
            groups_data = json.load(file)
        group = next((g for g in groups_data if g.get('name') == target_group_name), None)
        if group and group.get('locations'):
            # Return the first enabled location's slug
            for loc in group['locations']:
                if loc.get('enabled', True):
                    return loc.get('slug').rstrip('/')
    except Exception as e:
        errlog(f"Error reading groups.json: {e}")
    return None

def fetch_json_from_onion_url(url):
    try:
        stdlog(f"Fetching {target_group_name} API: {url}")
        response = requests.get(url, proxies=proxies, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        errlog(f"Bert API Error: {e}")
        return None

def main():
    base_url = get_base_url()
    if not base_url:
        # Fallback to hardcoded if DB is empty, or just error out
        base_url = 'http://hahahasrzrdb6bbg6aoxbgd47fxd4icuvucncmeldsjgnvdzoze2egid.onion'
        stdlog(f"Group '{target_group_name}' not found in DB or no enabled location. Using fallback.")

    full_api_url = urljoin(base_url + '/', api_endpoint.lstrip('/'))
    json_data = fetch_json_from_onion_url(full_api_url)
    
    if json_data and isinstance(json_data, list):
        for item in json_data:
            try:
                title = item.get('title', '').strip()
                title = re.sub(r"\s*\(UPDATE \d{1,2}/\d{1,2}/\d{4}\)", "", title)
                description = item.get('short_desc', '')
                date = item.get('createdAt', '')
                dt = datetime.fromisoformat(date.replace("Z", "+00:00")) 
                formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                
                # Construct post URL based on current base_url
                post_url = urljoin(base_url + '/', f"post/{item.get('id', '')}")
                
                appender(title, target_group_name, description, '', formatted_timestamp, post_url)
            except Exception as e:
                errlog(f"Error parsing item: {e}")

if __name__ == "__main__":
    main()
