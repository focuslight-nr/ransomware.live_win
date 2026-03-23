"""
    Parser for ALP-001
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

target_group_name = "alp-001"
base_url = "http://qthem3ogqqixjhhwacto6pqbjfy2vcykdlz7woulnewsrwy4lfjocfqd.onion"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('alp-001-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                articles = soup.find_all('div', class_='article-item')
                for article in articles:
                    try:
                        title_tag = article.find('h3')
                        if not title_tag:
                            continue
                        victim = title_tag.text.strip()
                        
                        description = ""
                        country = ""
                        
                        p_tags = article.find_all('p')
                        for p in p_tags:
                            # Using get_text with separator to avoid merged lines
                            p_text = p.get_text(separator="\n").strip()
                            if "Deadline:" in p_text:
                                continue
                            
                            if "Country:" in p_text:
                                lines = p_text.split('\n')
                                for line in lines:
                                    line_clean = line.strip()
                                    if line_clean.lower().startswith("country:"):
                                        country = line_clean[len("country:"):].strip()
                            
                            if description:
                                description += "\n" + p_text
                            else:
                                description = p_text
                        
                        website = ""
                        if "." in victim and " " not in victim:
                            website = victim
                        
                        link_tag = article.find('a', class_='sample-btn', href=True)
                        post_url = ""
                        if link_tag and link_tag['href'] != "#":
                            post_url = urljoin(base_url, link_tag['href'])
                        
                        appender(victim, target_group_name, description, website, "", post_url, country)
                    except Exception as e:
                        errlog(f'{target_group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
