import os
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
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


def looks_like_domain(value):
    return bool(re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", value.strip().lower()))


def normalize_website(title, website):
    website = website.strip()
    if website.lower() == "example.com":
        website = ""
    if not website and looks_like_domain(title):
        website = title
    return website


def extract_country(flag_img):
    alt = (flag_img.get("alt") or "").strip()
    if alt.endswith(" flag"):
        return alt[:-5].upper()
    return alt.upper()

def main():
    group_name = "killsecurity3.0"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith(group_name + '-'):
                html_doc = tmp_dir / filename
                stdlog(f"Parsing: {html_doc}")
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
                if base_url:
                    base_url = base_url.rstrip('/')

                items = soup.select("div.h-\\[200px\\].rounded-\\[10px\\]")

                for item in items:
                    try:
                        name_tag = item.find("span", class_=lambda c: c and "text-xl" in c)
                        if not name_tag:
                            continue
                        title = name_tag.get_text(strip=True)

                        website = ""
                        website_tag = item.find("span", class_=lambda c: c and "text-[10px]" in c)
                        if website_tag:
                            website = website_tag.get_text(strip=True)
                        website = normalize_website(title, website)

                        description = ""
                        desc_tag = item.find("div", class_=lambda c: c and "text-xs" in c)
                        if desc_tag:
                            description = desc_tag.get_text(strip=True)
                            if description == "No description given.":
                                description = ""

                        country = ""
                        flag_img = item.find("img", alt=re.compile(r"flag", re.I))
                        if flag_img:
                            country = extract_country(flag_img)

                        published = ""
                        status_tag = item.find("div", class_=lambda c: c and "text-[11px]" in c and "text-right" in c)
                        if status_tag:
                            published = status_tag.get_text(strip=True)

                        price = ""
                        disclosures = ""
                        labels = [div.get_text(strip=True) for div in item.find_all("div")]
                        for idx, text in enumerate(labels[:-1]):
                            if text == "Price":
                                price = labels[idx + 1]
                            elif text == "Disclosures":
                                disclosures = labels[idx + 1]

                        extra_infos = {}
                        if price:
                            extra_infos["price"] = price
                        if disclosures:
                            extra_infos["disclosures"] = disclosures

                        link = urljoin(base_url + "/", "targets") if base_url else ""

                        appender(title, group_name, description, website, published, link, country, extra_infos)
                    except Exception as e:
                        errlog(f"{group_name} - item parse fail: {e}")
        except Exception as e:
            errlog(f"{group_name} - file process fail: {e} in file: {filename}")

if __name__ == "__main__":
    main()
