#!/usr/bin/env python3

import os
import re
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

GROUP_NAME = "global secret"
FILE_PREFIX = "globalsecret"


def build_post_url(html_doc: Path, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href

    slug = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(str(html_doc))) or ""
    if not slug:
        return href
    return urljoin(slug.rstrip("/") + "/", href.lstrip("/"))


def extract_website(description: str) -> str:
    match = re.search(r"Website:\s*([^\s|]+)", description)
    if not match:
        return ""
    return re.sub(r"^https?://", "", match.group(1).strip(), flags=re.I).rstrip("/")


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{FILE_PREFIX}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing: {html_doc}")

        with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
            soup = BeautifulSoup(file, "html.parser")

        cards = soup.select("a.project-card")
        if not cards:
            stdlog(f"{GROUP_NAME} - no project cards found in {filename}")
            continue

        for card in cards:
            victim_tag = card.select_one(".card-title")
            if not victim_tag:
                continue

            victim = victim_tag.get_text(" ", strip=True)
            if not victim:
                continue

            country_tag = card.select_one(".card-country")
            revenue_tag = card.select_one(".card-revenue")
            status_tag = card.select_one(".card-status")
            description_tag = card.select_one(".card-description")

            description_parts = []
            if status_tag:
                description_parts.append(f"Status: {status_tag.get_text(' ', strip=True)}")
            if revenue_tag:
                description_parts.append(revenue_tag.get_text(" ", strip=True))
            if description_tag:
                description_parts.append(description_tag.get_text(" ", strip=True))

            description = " | ".join(part for part in description_parts if part)

            appender(
                victim=victim,
                group_name=GROUP_NAME,
                description=description,
                website=extract_website(description_tag.get_text(" ", strip=True) if description_tag else ""),
                published="",
                post_url=build_post_url(html_doc, card.get("href", "").strip()),
                country=country_tag.get_text(" ", strip=True) if country_tag else "",
            )


if __name__ == "__main__":
    main()
