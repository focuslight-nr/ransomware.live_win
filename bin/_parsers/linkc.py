"""
    From Template v4 - 202412827
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os,datetime,sys,re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender,extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME")
tmp_dir = Path(home + os.getenv("TMP_DIR"))

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "linkc"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Get base URL for links
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url: base_url = base_url.rstrip('/')

                cards = soup.find_all('div', class_='card')
                for card in cards:
                    try:
                        # Extract the title - the HTML uses 'cart-text'
                        title_tag = card.find('div', class_=re.compile(r'car[dt]-text card-title'))
                        if not title_tag: continue
                        title = title_tag.get_text(strip=True) 
                        
                        # Extract the link
                        link = ""
                        link_tag = card.find('a', class_='card-logo')
                        if link_tag and base_url:
                            link = base_url + link_tag['href']
                        
                        # Extract the date
                        published = ""
                        date_tag = card.find("div", attrs={"cds-text": "caption"})
                        if not date_tag:
                            date_tag = card.find("div", class_="card-text")
                        
                        if date_tag:
                            date_str = date_tag.get_text(strip=True)
                            # Format: "Feb 28, 2026, 1:12:25 AM"
                            try:
                                # Clean up extra whitespace/newlines
                                date_str = re.sub(r'\s+', ' ', date_str).strip()
                                parsed_date = datetime.strptime(date_str, "%b %d, %Y, %I:%M:%S %p")
                                published = parsed_date.strftime("%Y-%m-%d %H:%M:%S.%f")
                            except:
                                published = date_str
                        
                        # Extract the description
                        description_tag = card.find('div', class_='card-description')
                        description = description_tag.get_text(strip=True) if description_tag else ''

                        appender(title, group_name, description, '', published, link)
                    except Exception as e:
                        errlog(f"{group_name} - card parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")