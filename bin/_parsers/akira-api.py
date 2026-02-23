"""
    Upgraded API Parser for Akira
"""

import os
import json
import requests
import urllib3
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

target_group_name = "akira"

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

def get_csrf_session(base_url):
    try:
        stdlog(f"Fetching CSRF for {target_group_name}: {base_url}")
        response = requests.get(base_url, proxies=proxies, verify=False, timeout=45)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_element = soup.find('meta', {'name': 'csrf-token'})
        csrf_token = csrf_element['content'] if csrf_element and 'content' in csrf_element.attrs else None
        return csrf_token, response.cookies
    except Exception as e:
        errlog(f"CSRF fetch failed for {base_url}: {e}")
        return None, None

def fetch_json(url, csrf_token, cookies, base_url):
    headers = {
        "Referer": base_url + '/',
        "X-CSRF-Token": csrf_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        response = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, verify=False, timeout=45)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        errlog(f"JSON fetch failed for {url}: {e}")
        return None

def main():
    base_urls = get_base_urls()
    if not base_urls:
        stdlog(f"No enabled locations found for {target_group_name} in DB.")
        base_urls = ['https://akiral2iz6a7qgd3ayp3l6yub7xx2uep76idk3u2kollpj5z3z636bad.onion']

    for base_url in base_urls:
        csrf_token, cookies = get_csrf_session(base_url)
        if not csrf_token or not cookies:
            continue

        # News
        news_data = fetch_json(urljoin(base_url + '/', 'n'), csrf_token, cookies, base_url)
        if news_data and "objects" in news_data:
            for entry in news_data["objects"]:
                title = entry.get('title', '').replace('\n','')
                description = entry.get('content', '')
                date = entry.get('date', '') + " 00:00:00.000000" if entry.get('date') else ""
                appender(title, target_group_name, description, '', date, '')

        # Leaks
        leak_data = fetch_json(urljoin(base_url + '/', 'l'), csrf_token, cookies, base_url)
        if leak_data and "objects" in leak_data:
            for entry in leak_data["objects"]:
                title = entry.get('name', '').replace('\n','')
                description = entry.get('desc', '')
                appender(title, target_group_name, description)
        
        if news_data or leak_data:
            return # Success

if __name__ == "__main__":
    main()
