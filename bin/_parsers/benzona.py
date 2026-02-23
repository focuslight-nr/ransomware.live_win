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
GROUP_NAME = "benzona"
URL = "http://benzona6x5ggng3hx52h4mak5sgx5vukrdlrrd3of54g2uppqog2joyd.onion"

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
    
    # Find all victim cards
    victim_cards = soup.find_all('div', class_='victim-card')
    
    if not victim_cards:
        errlog(f"[{GROUP_NAME}] ❌ Could not find any victim cards.")
        return

    # Process each victim card
    for card in victim_cards:
        victim_name_tag = card.find('h3')
        if not victim_name_tag:
            continue
        
        victim_name = victim_name_tag.text.strip()
        
        # Gather details from <p> tags for the description
        details = []
        for p_tag in card.find_all('p'):
            details.append(p_tag.text.strip())
        description = ' | '.join(details)

        # No individual post URL or publication date is available on the card
        # Use the main URL and current time
        post_url = URL
        published = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Append the victim data
        appender(
            victim=victim_name,
            group_name=GROUP_NAME,
            description=description,
            published=published,
            post_url=post_url,
            website=victim_name # Assume the h3 title is the website
        )

    stdlog(f"[{GROUP_NAME}] Parser finished.")

if __name__ == "__main__":
    main()