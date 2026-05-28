"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |     X     |          |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, sys, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('nightspire-'):
                html_doc = tmp_dir / filename
                file = open(html_doc, "r", encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(file, 'html.parser')

                cards = soup.find_all('div', class_='team-card')
                for card in cards:
                    # Extract title
                    title_tag = card.find('a', class_='team-name')
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Remove trailing ", Country" or "(Country)" from title
                    ##title = re.sub(r'\s*\([^)]+\)\s*$', '', title)
                    ##title = re.sub(r',\s*[A-Z][a-zA-Z\s]+$', '', title)
                    ##title = title.strip()

                    # Extract website from href (skip empty, space-only, or non-URL hrefs)
                    website = ''
                    href = title_tag.get('href', '').strip()
                    if href and href.startswith('http'):
                        website = href

                    # Extract country code from flag image URL (flagcdn.com/w320/{cc}.png)
                    country_code = ''
                    flag_img = card.find('img', class_='team-img', src=re.compile(r'flagcdn\.com'))
                    if flag_img:
                        flag_match = re.search(r'flagcdn\.com/w320/([a-z]{2})\.png', flag_img.get('src', ''))
                        if flag_match:
                            country_code = flag_match.group(1).upper()

                    # Extract description from target_info paragraph
                    description = ''
                    info_p = card.find('p', id=re.compile(r'^target_info_'))
                    if info_p:
                        desc_text = info_p.get_text(strip=True).replace('\n', ' ')
                        if desc_text:
                            description = desc_text
                    if desc_text == 'Data is not available.':
                        description = ''
                      
                    # Extract published date from 🧭 date paragraph
                    published = ''
                    for p_tag in card.find_all('p', class_='team-bio'):
                        text = p_tag.get_text(strip=True)
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                        if date_match:
                            try:
                                dt = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                if dt > datetime(2026, 1, 31):
                                    published = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
                                else:
                                    published = ''
                            except ValueError:
                                pass
                            break

                    # Extract data size from selling/countdown span (e.g. "$500 Selling (200GB)")
                    data_size = ''
                    selling_span = card.find('span', class_='text-red-600')
                    if selling_span:
                        size_match = re.search(r'\(([^)]+)\)', selling_span.get_text())
                        if size_match:
                            data_size = size_match.group(1)

                    if not published:
                        continue

                    extra_infos = {}
                    if data_size:
                        extra_infos['data_size'] = data_size

                    appender(title, 'nightspire', description, website, published, '', country_code, extra_infos)
                    #print('title:', title)
                    #print('description:', description)
                    #print('website:', website)
                    #print('published:', published)
                    #print('country_code:', country_code)
                    #print('data_size:', data_size)
                    #print('*'*20)
                    

                if not cards:
                    for card in soup.select('.say-card'):
                        title_tag = card.find('h3')
                        text_tag = card.select_one('.text')
                        if not title_tag or not text_tag:
                            continue

                        title_text = title_tag.get_text(" ", strip=True)
                        description = text_tag.get_text(" ", strip=True)
                        victim = ""

                        warning = re.search(r'warning to\s+(?:the\s+)?(.+?)\s*(?:☠|$)', title_text, re.I)
                        if warning:
                            victim = warning.group(1).strip()

                        if not victim:
                            strong = text_tag.find('strong')
                            if strong:
                                candidate = strong.get_text(" ", strip=True)
                                if len(candidate.split()) > 1 and candidate.lower() not in {"police", "fbi"}:
                                    victim = candidate

                        if not victim or victim.lower().startswith('nightspire'):
                            continue

                        appender(victim, 'nightspire', description, '', '', '', '')

                file.close()
        except:
            errlog('nightspire : parsing fail')
