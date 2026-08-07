#!/usr/bin/env python3

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, stdlog


GROUP_NAME = "gammax"
FILE_PREFIX = "gammax"

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def post_url(html_doc: Path, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    base = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(html_doc.name)) or ""
    return urljoin(base.rstrip("/") + "/", href.lstrip("/")) if base else href


def parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return value


def main():
    for html_doc in sorted(tmp_dir.glob(f"{FILE_PREFIX}-*.html")):
        stdlog(f"Parsing: {html_doc}")
        soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        cards = soup.select("article.post-card")
        if not cards:
            stdlog(f"{GROUP_NAME} - no post cards found in {html_doc.name}")
            continue

        for card in cards:
            title = card.select_one(".post-title")
            if not title or not (victim := title.get_text(" ", strip=True)):
                continue
            website = card.select_one("a.title-link[href]")
            detail = card.select_one("a.post-card-link[href]")
            excerpt = card.select_one(".post-excerpt")
            published = card.select_one("time.post-date")
            appender(
                victim=victim,
                group_name=GROUP_NAME,
                description=excerpt.get_text(" ", strip=True) if excerpt else "",
                website=website["href"] if website else "",
                published=parse_date(published.get_text(" ", strip=True)) if published else "",
                post_url=post_url(html_doc, detail["href"] if detail else ""),
            )


if __name__ == "__main__":
    main()
