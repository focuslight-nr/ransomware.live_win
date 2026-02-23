#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# Add the parent directory of the current script's directory to the Python path
# to ensure that shared_utils can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils import stdlog, errlog, appender

# Group-specific details
GROUP_NAME = "bashe"
URL = "http://basheqtvzqwz4vp6ks5lm2ocq7i6tozqgf6vjcasj4ezmsy4bkpshhyd.onion"

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
    
    # Find all victim segments
    victim_segments = soup.find_all('div', class_='segment')
    
    if not victim_segments:
        errlog(f"[{GROUP_NAME}] ❌ Could not find any victim segments.")
        return

    # Process each victim segment
    for segment in victim_segments:
        try:
            victim_name = segment.find('div', class_='segment__text__off').text.strip()
            country = segment.find('div', class_='segment__country__deadline').text.strip()
            description = segment.find('div', class_='segment__text__dsc').text.strip()
            
            # Extract and parse the published date
            date_text = segment.find('div', class_='segment__date__deadline').text
            date_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})', date_text)
            if date_match:
                published_dt = datetime.strptime(date_match.group(1), '%Y/%m/%d %H:%M:%S')
                published = published_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                published = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # Extract post URL from onclick attribute
            onclick_attr = segment.get('onclick', '')
            url_match = re.search(r"window\.location\.href='(.*?)'", onclick_attr)
            if url_match:
                post_url = URL + url_match.group(1)
            else:
                post_url = URL

            # Append the victim data
            appender(
                victim=victim_name,
                group_name=GROUP_NAME,
                description=description,
                published=published,
                post_url=post_url,
                country=country,
                website=victim_name # Assume the name is the website
            )
        except Exception as e:
            errlog(f"[{GROUP_NAME}] ❌ Error parsing a segment: {e} - Segment: {segment.text.strip()}")

    stdlog(f"[{GROUP_NAME}] Parser finished.")

if __name__ == "__main__":
    main()
