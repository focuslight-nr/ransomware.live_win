"""
    Parser for Prinz Eugen
"""

import os
import datetime
from bs4 import BeautifulSoup
from shared_utils import appender, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

target_group_name = "prinzeugen"

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith(f'{target_group_name}-'):
            html_doc = tmp_dir / filename
            stdlog(f'Parsing: {html_doc}')
            try:
                with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f, "html.parser")

                sections = soup.find_all("section", class_="landing-shell--portal")
                for section in sections:
                    try:
                        # Victim Name
                        name_tag = section.find("h2", class_="landing-portal-frame__name")
                        victim = name_tag.get_text(strip=True) if name_tag else "N/A"

                        # Website (Optional)
                        website_tag = section.find("span", class_="warn")
                        website = website_tag.get_text(strip=True) if website_tag else ""

                        # Description
                        desc_tag = section.find("p", class_="landing-desc")
                        description = desc_tag.get_text(strip=True) if desc_tag else ""

                        # Published Date (Start Date in this case)
                        published = ""
                        meta_rows = section.find_all("div", class_="landing-portal-frame__meta-row")
                        for row in meta_rows:
                            label = row.find("dt", class_="landing-portal-frame__meta-label")
                            value = row.find("dd", class_="landing-portal-frame__meta-value")
                            if label and "Start Date" in label.get_text():
                                date_str = value.get_text(strip=True) if value else ""
                                try:
                                    # Example: "February 27, 2026"
                                    dt = datetime.datetime.strptime(date_str, "%B %d, %Y")
                                    published = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    published = date_str # Fallback to raw string
                                break

                        # Post URL
                        action_tag = section.find("a", class_="landing-portal-frame__action")
                        post_url = action_tag["href"] if action_tag and action_tag.has_attr("href") else ""

                        appender(
                            victim=victim,
                            group_name=target_group_name,
                            description=description,
                            website=website,
                            published=published,
                            post_url=post_url
                        )
                    except Exception as e:
                        errlog(f'{target_group_name} - error parsing item: {e}')
            except Exception as e:
                errlog(f'{target_group_name} - error reading file {filename}: {e}')

if __name__ == "__main__":
    main()
