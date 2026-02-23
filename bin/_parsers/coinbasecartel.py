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
GROUP_NAME = "coinbasecartel"
URL = "http://fjg4zi4opkxkvdz7mvwp7h6goe4tcby3hhkrz43pht4j3vakhy75znyd.onion"

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
    
    # Find all victim articles
    victim_articles = soup.find_all('article', class_='company-row')
    
    if not victim_articles:
        errlog(f"[{GROUP_NAME}] ❌ Could not find any victim articles.")
        return

    # Process each victim article
    for article in victim_articles:
        try:
            victim_name_tag = article.find('h3', class_='company-name')
            if not victim_name_tag:
                continue
            victim_name = victim_name_tag.text.replace('\u2019', "'").replace('</span>', '').strip()

            website_tag = article.find(class_='company-website')
            website = website_tag.text.strip() if website_tag else ''

            description_tag = article.find('p', class_='company-row-desc')
            description = description_tag.text.strip() if description_tag else ''

            post_url_tag = article.find('a', class_='btn-primary')
            if post_url_tag and post_url_tag.get('href'):
                post_url = URL + post_url_tag['href']
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
                website=website
            )
        except Exception as e:
            errlog(f"[{GROUP_NAME}] ❌ Error parsing an article: {e} - Article: {article.text.strip()}")

    stdlog(f"[{GROUP_NAME}] Parser finished.")

if __name__ == "__main__":
    main()
