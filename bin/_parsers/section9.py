#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def build_post_url(html_doc: Path, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href

    slug = find_slug_by_md5("section9", extract_md5_from_filename(str(html_doc))) or ""
    if not slug:
        return href
    return urljoin(slug.rstrip("/") + "/", href.lstrip("/"))


def main():
    group_name = "section9"

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{group_name}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing: {html_doc}")

        with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
            soup = BeautifulSoup(file, "html.parser")

        cards = soup.select("a.card")
        if not cards:
            stdlog(f"{group_name} - no cards found in {filename}")
            continue

        for card in cards:
            victim_tag = card.select_one(".card-title")
            if not victim_tag:
                continue

            victim = victim_tag.get_text(" ", strip=True)
            if not victim:
                continue

            sector_tag = card.select_one(".card-summary")
            country_tag = card.select_one(".country")
            countdown_tag = card.select_one(".countdown")

            description_parts = []
            if sector_tag:
                description_parts.append(f"Sector: {sector_tag.get_text(' ', strip=True)}")
            if countdown_tag:
                description_parts.append(countdown_tag.get_text(" ", strip=True))

            appender(
                victim=victim,
                group_name=group_name,
                description=" | ".join(description_parts),
                website="",
                published="",
                post_url=build_post_url(html_doc, card.get("href", "").strip()),
                country=country_tag.get_text(" ", strip=True) if country_tag else "",
            )


if __name__ == "__main__":
    main()
