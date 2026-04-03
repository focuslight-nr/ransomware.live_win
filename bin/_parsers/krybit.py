"""
    Parser for KRYBIT
"""

import os, re
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, tmp_dir
from datetime import datetime
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
base_url = "http://krybitqsdzwmhnitvwuhvsntfgf2wrhxveyxroxpc44c6gkft2cqldyd.onion"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('krybit-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing krybit: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                cards = soup.find_all('div', class_='post-card')
                for card in cards:
                    try:
                        title_tag = card.find('h3', class_='post-title')
                        if not title_tag:
                            continue
                        victim = title_tag.text.strip()
                        
                        desc_tag = card.find('div', class_='post-excerpt')
                        description = desc_tag.text.strip() if desc_tag else ""
                        
                        # Published date: use timer-display data-end as a placeholder for the leak date
                        timer_tag = card.find('div', class_='timer-display')
                        published = ""
                        if timer_tag and timer_tag.get('data-end'):
                            try:
                                timestamp = int(timer_tag.get('data-end'))
                                published = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                pass

                        # Extract link from onclick
                        post_url = ""
                        onclick = card.get('onclick')
                        if onclick:
                            match = re.search(r"window.location='(.*?)'", onclick)
                            if match:
                                post_url = urljoin(base_url, match.group(1))

                        appender(victim, 'krybit', description, "", published, post_url)
                    except Exception as e:
                        errlog(f'krybit - error parsing card: {e}')
            except Exception as e:
                errlog(f'krybit - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
