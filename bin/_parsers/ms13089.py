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
GROUP_NAME = "ms13-089"
URL = "http://msleakjir7pxbe6onlqe5uwgvdmy6nq4mnwfy7ojswbhnleenm77vgad.onion"

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
        try:
            title_block = post.find('div', class_='post-title-block')
            if not title_block:
                continue
            
            title_div = title_block.find('div')
            full_title = title_div.text.strip()
            
            # Extract victim name and country
            victim_name = full_title
            country = ''
            match = re.search(r'\((.*?)\)', full_title)
            if match:
                victim_name = full_title[:match.start()].strip()
                country_info = match.group(1).split(',')[0].strip()
                country = country_info

            description_tag = post.find('div', class_='post-text')
            description = description_tag.text.strip() if description_tag else ''

            post_url_tag = post.find('a', class_='post-more-link')
            if post_url_tag and post_url_tag.get('onclick'):
                onclick_attr = post_url_tag['onclick']
                url_match = re.search(r"location\.href='(.*?)'", onclick_attr)
                if url_match:
                    post_url = URL + url_match.group(1)
                else:
                    post_url = URL
            else:
                post_url = URL

            # No publication date on the main page, use current time
            published = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            appender(
                victim=victim_name,
                group_name=GROUP_NAME,
                description=description,
                published=published,
                post_url=post_url,
                country=country,
                website=victim_name
            )
        except Exception as e:
            errlog(f"[{GROUP_NAME}] ❌ Error parsing a post: {e} - Post: {post.text.strip()}")

    stdlog(f"[{GROUP_NAME}] Parser finished.")

if __name__ == "__main__":
    main()
