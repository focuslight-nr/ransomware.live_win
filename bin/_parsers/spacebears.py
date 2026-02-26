"""
    Parser for Space Bears
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def parse_relative_date(date_text):
    """
    Parses strings like 'Published 1 week ago', 'Published 2 days ago', etc.
    """
    now = datetime.now()
    date_text = date_text.lower()
    match = re.search(r'(\d+)\s+(year|month|week|day|hour|minute)s?\s+ago', date_text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == 'year':
            return now - timedelta(days=amount * 365)
        elif unit == 'month':
            return now - timedelta(days=amount * 30)
        elif unit == 'week':
            return now - timedelta(weeks=amount)
        elif unit == 'day':
            return now - timedelta(days=amount)
        elif unit == 'hour':
            return now - timedelta(hours=amount)
        elif unit == 'minute':
            return now - timedelta(minutes=amount)
    return now

def main():
    target_group = "spacebears"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f"{target_group}-"):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing {target_group}: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                items = soup.find_all('div', class_='companies-list__item')
                for item in items:
                    try:
                        name_tag = item.find('div', class_='name')
                        if not name_tag:
                            continue
                        name_a = name_tag.find('a')
                        victim = name_a.text.strip() if name_a else name_tag.text.strip()
                        post_url = name_a['href'] if name_a and name_a.has_attr('href') else ""

                        text_div = item.find('div', class_='text')
                        description = ""
                        website = ""
                        if text_div:
                            # Try to find website link
                            ws_a = text_div.find('a', href=True)
                            if ws_a:
                                website = ws_a['href']
                            
                            # Clean up description
                            description = text_div.get_text(separator=" ", strip=True)
                            if website and website in description:
                                description = description.replace(website, "").strip()

                        # Date parsing
                        published = ""
                        image_block = item.find('div', class_='image-block')
                        if image_block:
                            p_tags = image_block.find_all('p')
                            for p in p_tags:
                                if "Published" in p.text:
                                    dt = parse_relative_date(p.text)
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                    break
                        
                        # Fallback for date if relative parsing fails
                        if not published:
                            countdown = item.find('div', class_='countdown')
                            if countdown and countdown.has_attr('data-date'):
                                # data-date seems to be the deadline/release date
                                published = countdown['data-date']

                        appender(victim, target_group, description, website, published, post_url)
                    except Exception as e:
                        errlog(f'{target_group} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()

