#!/usr/bin/env python3

import os
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, stdlog


GROUP_NAME = "orova"
FILE_PREFIX = "orova"

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return value


def main():
    for html_doc in sorted(tmp_dir.glob(f"{FILE_PREFIX}-*.html")):
        stdlog(f"Parsing: {html_doc}")
        soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        cards = soup.select("article.card-elevated")
        if not cards:
            stdlog(f"{GROUP_NAME} - no victim cards found in {html_doc.name}")
            continue

        for card in cards:
            title = card.select_one("h3[title]")
            if not title or not (victim := title.get_text(" ", strip=True)):
                continue
            links = card.select("a[href]")
            website = next((link["href"] for link in links if link.get_text(" ", strip=True) == "Company URL"), "")
            post_url = next((link["href"] for link in links if link.get_text(" ", strip=True) == "Watch Data"), "")
            country = card.select_one("div[title] span.truncate")
            category = card.select_one("span.text-accent-hover")
            description = card.select_one("p.line-clamp-4")
            published = card.select_one("div.text-text-muted")
            details = [
                category.get_text(" ", strip=True) if category else "",
                description.get_text(" ", strip=True) if description else "",
            ]
            appender(
                victim=victim,
                group_name=GROUP_NAME,
                description=" | ".join(part for part in details if part),
                website=website,
                published=parse_date(published.get_text(" ", strip=True)) if published else "",
                post_url=post_url,
                country=country.get_text(" ", strip=True) if country else "",
            )


if __name__ == "__main__":
    main()
