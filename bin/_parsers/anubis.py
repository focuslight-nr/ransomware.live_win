"""
    From Template v4 - 202412827
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |         |           |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os,datetime,sys,re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from urllib.parse import urljoin
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("../.env")
load_dotenv(dotenv_path=env_path)
home = os.getenv("RANSOMWARELIVE_HOME")
tmp_dir = Path(home + os.getenv("TMP_DIR"))

def main():

    # Define the date format to convert to
    date_format = "%Y-%m-%d %H:%M:%S.%f"
    
    ## Get the ransomware group name from the script name 
    script_path = os.path.abspath(__file__)
    # If it's a symbolic link find the link source 
    if os.path.islink(script_path):
        original_path = os.readlink(script_path)
        if not os.path.isabs(original_path):
            original_path = os.path.join(os.path.dirname(script_path), original_path)
        original_path = os.path.abspath(original_path)
        original_name = os.path.basename(original_path)
        group_name = original_name.replace('.py','')
    # else get the script name 
    else:
        script_name = os.path.basename(script_path)
        group_name = script_name.replace('.py','')

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name+'-'):
                html_doc= tmp_dir / filename
                file=open(html_doc, 'r', encoding='utf-8')
                soup=BeautifulSoup(file,'html.parser')
                # Find all victim containers directly
                victim_items = soup.find_all("div", class_="col-sm-4 p-2")
                if victim_items:
                    stdlog(f"Found {len(victim_items)} items for {group_name}")
                    # Get base URL
                    md5_val = extract_md5_from_filename(str(html_doc))
                    base_url = find_slug_by_md5(group_name, md5_val)
                    if base_url:
                        base_url = base_url.rstrip('/')

                    for victim_div in victim_items:
                        try:
                            # Search within the inner div
                            inner_div = victim_div.find("div", class_="bg-secondary-2") or victim_div.find("div", class_="bg-secondary")
                            if not inner_div:
                                inner_div = victim_div

                            name_tag = inner_div.find("h5", class_="fw-bold mb-2")
                            if not name_tag:
                                continue
                            victim = name_tag.get_text(strip=True)
                            
                            description = ""
                            # The description is often the second h5 or has a specific style
                            h5_tags = inner_div.find_all("h5", class_="fw-bold mb-2")
                            if len(h5_tags) > 1:
                                description = h5_tags[1].get_text(strip=True)
                            
                            link_tag = inner_div.find("a", class_=re.compile(r"btn.*"))
                            post_url = ""
                            if link_tag and link_tag.has_attr("href"):
                                post_url = urljoin(base_url, link_tag["href"]) if base_url else link_tag["href"]
                        
                            appender(victim, group_name, description, "", "", post_url)
                        except Exception as e:
                            errlog(f'{group_name} - error parsing victim: {e}')
                else:
                    errlog(f"{group_name} - no items found in {filename}")
                file.close()
        except Exception as e:
            errlog(group_name + ' - parsing fail with error: ' + str(e) + 'in file:' + filename)
            