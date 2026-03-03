import os, re
from bs4 import BeautifulSoup
from datetime import datetime
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = "securotrop"
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

                # The HTML structure has victim items in <li> elements
                # Each item has an <h3> for the company name
                items = soup.find_all('li')
                for item in items:
                    try:
                        title_tag = item.find('h3')
                        if not title_tag:
                            continue
                        
                        title = title_tag.get_text(strip=True)
                        if not title:
                            continue

                        # Extract country
                        country = ""
                        country_img = item.find('img', alt=re.compile(r'flag'))
                        if country_img:
                            country_span = country_img.find_next('span')
                            if country_span:
                                country = country_span.get_text(strip=True)

                        # Extract description from Revenue, Employees, etc.
                        details = []
                        info_spans = item.find_all('span', class_=re.compile(r'text-\[14px\]'))
                        # Labels are spans with text-[10px]
                        labels = item.find_all('span', class_=re.compile(r'text-\[10px\]'))
                        
                        for i in range(min(len(labels), len(info_spans))):
                            label = labels[i].get_text(strip=True)
                            val = info_spans[i].get_text(strip=True)
                            if label not in ["United States", "Canada", "Germany", "United Kingdom"]: # Skip country label
                                details.append(f"{label}: {val}")
                        
                        description = " | ".join(details)
                        
                        # Extract "Published" status
                        published_tag = item.find('span', string=re.compile(r'Published'))
                        published = "Published" if published_tag else ""

                        # For SPA sites, actual post URLs are often dynamic, using base_url as placeholder
                        link = base_url

                        appender(title, group_name, description, '', published, link, country)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
