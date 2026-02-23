import os, datetime, sys, re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import appender, errlog

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME")
tmp_dir = Path(home + os.getenv("TMP_DIR"))



def main():
    target_group_name = 'blackbyte'

    for filename in os.listdir(tmp_dir):
        if filename.startswith(target_group_name + '-'):
            html_doc = tmp_dir / filename
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')

                # Try primary structure
                divs_name = soup.find_all('table', {"class": "table table-bordered table-content"})
                for div in divs_name:
                    try:
                        title_tag = div.find('h1')
                        if not title_tag: continue
                        title = title_tag.text.strip()
                        
                        desc_tag = div.find('p')
                        description = desc_tag.text.strip().replace("\n", "") if desc_tag else ""
                        
                        link_tag = div.find('a', href=True)
                        website = link_tag['href'] if link_tag else ""
                        
                        appender(title, target_group_name, description, website)
                    except Exception as e:
                        errlog(f'blackbyte - error parsing table item: {e}')

                # Try fallback structure (historical)
                tables = soup.find_all('table', class_='table')
                for table in tables:
                    try:
                        caption_tag = table.find('caption', class_='target-name')
                        if not caption_tag: continue
                        caption = caption_tag.text.strip()
                        
                        tbody = table.find('tbody')
                        if not tbody: continue
                        rows = tbody.find_all('tr')
                        if not rows: continue
                        
                        last_date_text = rows[-1].find('td').text.strip()
                        try:
                            last_date = datetime.strptime(last_date_text, '%Y-%m-%d %H:%M')
                            published = last_date.strftime('%Y-%m-%d %H:%M:%S.%f')
                        except:
                            published = ""
                            
                        appender(caption, target_group_name, '', '', published)
                    except Exception as e:
                        # Silently skip if it's not the intended table structure
                        pass

            except Exception as e:
                errlog(f'blackbyte - error reading file {filename}: {e}')
            