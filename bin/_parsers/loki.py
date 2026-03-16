"""
    Parser for Loki Ransomware Group
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog, tmp_dir, find_slug_by_md5, extract_md5_from_filename
from pathlib import Path

def main():
    group_name = "loki"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f'{group_name}-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # The victim list container
                victims_list = soup.find('div', id='victims-list')
                if not victims_list:
                    stdlog(f'No victims list found in {filename}')
                    continue
                
                # Extract MD5 and base URL
                md5_val = extract_md5_from_filename(filename)
                base_url = find_slug_by_md5(group_name, md5_val)
                if base_url:
                    base_url = base_url.rstrip('/')
                
                # Each victim is in a victim-item div
                victim_items = victims_list.find_all('div', class_='victim-item')
                for item in victim_items:
                    try:
                        name_tag = item.find('h4')
                        if not name_tag:
                            continue
                        victim = name_tag.text.strip()
                        
                        # In the current HTML structure, there's no direct description or link in the item list,
                        # but we can set the base_url as post_url.
                        description = ""
                        post_url = base_url if base_url else ""
                        
                        appender(victim, group_name, description, "", "", post_url)
                    except Exception as e:
                        errlog(f'{group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
