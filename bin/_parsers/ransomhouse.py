"""
    ransomhouse parser — JSON-in-<pre> format

    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |     X     |     X    |
    +-----------------------+-----------+----------+
    Rappel : def appender(post_title, group_name, description="", website="", published="", post_url="", country="")
"""

import os, json
from bs4 import BeautifulSoup
from datetime import datetime

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


def parse_pre_payload(pre, onion_host):
    date_format = "%d/%m/%Y"
    desired_format = "%Y-%m-%d %H:%M:%S.%f"
    data = json.loads(pre.get_text())

    for record in data.get('data', []):
        title = record.get('header', '')
        if not title or record.get('display') == 'animated':
            continue

        website = record.get('url', '')
        description = record.get('info', '')

        content_file = record.get('content', '')
        post_url = f'http://{onion_host}/{content_file}' if content_file else ''

        formated_date = ''
        action_date = record.get('actionDate', '')
        if action_date:
            try:
                datetime_obj = datetime.strptime(action_date, date_format)
                formated_date = datetime_obj.strftime(desired_format)
            except ValueError:
                pass

        appender(title, 'ransomhouse', description, website, formated_date, post_url)


def parse_current_html(soup, onion_host):
    for record in soup.select("div.cls_record"):
        anchor = record.find("a", href=True)
        title_node = record.select_one("div.cls_recordTop p")
        website_node = record.select_one("div.cls_recordMiddle p")
        if not anchor or not title_node:
            continue

        title = title_node.get_text(strip=True)
        if not title:
            continue

        website = website_node.get_text(strip=True) if website_node else ""
        description_parts = []
        published = ""

        for element in record.select("div.cls_recordBottomElement"):
            label_node = element.select_one("div.cls_headerSmall")
            label = label_node.get_text(" ", strip=True).rstrip(":") if label_node else ""
            values = [
                value.strip()
                for value in element.stripped_strings
                if value.strip() and value.strip() not in {label, f"{label}:"}
            ]
            if not label or not values:
                continue

            value = " ".join(values)
            if label.lower() == "action date":
                try:
                    published = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    pass
            else:
                description_parts.append(f"{label}: {value}")

        href = anchor.get("href", "")
        post_url = f"http://{onion_host}{href}" if href.startswith("/") else href
        appender(title, 'ransomhouse', " | ".join(description_parts), website, published, post_url)


def main():
    for filename in os.listdir(tmp_dir):
        try:
            if filename.startswith('ransomhouse-'):
                html_doc = tmp_dir / filename

                with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f, 'html.parser')

                onion_host = 'zohlm7ahjwegcedoz7lrdrti7bvpofymcayotp744qhx6gjmxbuo2yid.onion'

                pre = soup.find('pre')
                if pre:
                    parse_pre_payload(pre, onion_host)
                    continue

                records = soup.select("div.cls_record")
                if not records:
                    errlog(f'ransomhouse: no known record structure found in {filename}')
                    continue

                parse_current_html(soup, onion_host)

        except Exception as e:
            errlog(f'ransomhouse: parsing fail with error {e}')
