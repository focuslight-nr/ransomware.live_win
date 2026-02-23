#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# Add the parent directory of the current script's directory to the Python path
# to ensure that shared_utils can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils import stdlog, errlog, appender

# Group-specific details
GROUP_NAME = "arachnaleak"
URL = "http://ptyctpveqfevlukjw4hpdh6nb5oiemq6ek6tuuvxbtrfghvuutvscsid.onion"

PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

def main():
    stdlog(f"[{GROUP_NAME}] Starting parser")
    
    try:
        # Fetch the main page
        response = requests.get(URL, proxies=PROXIES, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        errlog(f"[{GROUP_NAME}] ❌ Error fetching page: {e}")
        return

    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all victim posts
    victim_posts = soup.find_all('div', class_='post')
    
    if not victim_posts:
        errlog(f"[{GROUP_NAME}] ❌ Could not find any victim posts.")
        return

    # Process each victim post
    for post in victim_posts:
        victim_name_tag = post.find('h2')
        if not victim_name_tag:
            continue
        
        victim_name = victim_name_tag.text.strip()
        
        # No description or publication date available on the main page
        description = ""
        post_url = URL # No individual post URLs
        published = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Append the victim data
        appender(
            victim=victim_name,
            group_name=GROUP_NAME,
            description=description,
            published=published,
            post_url=post_url,
            website="" 
        )

    stdlog(f"[{GROUP_NAME}] Parser finished.")

if __name__ == "__main__":
    main()
