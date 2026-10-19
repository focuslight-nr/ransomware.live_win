"""Parse Everest's current Chronicle and its older category listing."""

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5


home = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=home / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", ".")) / os.getenv("TMP_DIR", "tmp").strip("/")


def _published(date_text):
    """Use dates only when the page supplies the year; relative dates are unstable."""
    try:
        return datetime.strptime(date_text.strip(), "%d %b %Y").strftime("%Y-%m-%d %H:%M:%S.%f")
    except (AttributeError, ValueError):
        return ""


def _parse_chronicle(soup, base_url):
    page_script = soup.select_one('script[data-page="app"]')
    if not page_script or not page_script.string:
        return False
    try:
        page = json.loads(page_script.string)
    except json.JSONDecodeError:
        return False
    if page.get("component") != "Public/News":
        return False
    props = page.get("props")
    categories = props.get("categories") if isinstance(props, dict) else None
    if not isinstance(categories, list):
        return False

    for category in categories:
        if not isinstance(category, dict):
            continue
        title = category.get("title")
        slug = category.get("slug")
        if not isinstance(title, str) or not title.strip() or not isinstance(slug, str) or not slug.strip():
            continue
        if slug == "negotiation-rules":
            continue
        post_url = urljoin(base_url.rstrip("/") + "/", "news/" + slug.strip("/"))
        appender(title.strip(), "everest", published=_published(category.get("date")), post_url=post_url)
    return True


def _parse_legacy(soup, base_url):
    for div in soup.select("div.category-item.js-open-chat"):
        title_tag = div.select_one("div.category-title")
        slug = div.get("data-translit")
        if not title_tag or not slug:
            continue
        title = title_tag.get_text(strip=True)
        title = title.replace("- Database Leaked", "")
        title = title.replace(" DataBase on sale for $1 Million", "")
        if title == "Total Patient Care LLC;A Sensitive Touch Home Health;Alphastar Home Health Care;Heart of Texas Home Healthcare Services Inc Data Leak":
            continue
        date_tag = div.select_one("div.category-date")
        published = _published(date_tag.get_text(strip=True)) if date_tag else ""
        post_url = urljoin(base_url.rstrip("/") + "/", "news/" + slug.strip("/") + "/")
        appender(title, "everest", published=published, post_url=post_url)


def main():
    for html_doc in sorted(tmp_dir.glob("everest-*.html")):
        try:
            base_url = find_slug_by_md5("everest", extract_md5_from_filename(html_doc.name))
            if not base_url:
                errlog("Everest - unknown source for " + html_doc.name)
                continue
            with html_doc.open(encoding="utf-8", errors="ignore") as source:
                soup = BeautifulSoup(source, "html.parser")
            if not _parse_chronicle(soup, base_url):
                _parse_legacy(soup, base_url)
        except Exception as exc:
            errlog("Everest - parsing fail with error: " + str(exc) + " in file: " + html_doc.name)
