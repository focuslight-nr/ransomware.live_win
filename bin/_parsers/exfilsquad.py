#!/usr/bin/env python3

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

GROUP_NAME = "exfilsquad"


def build_post_url(html_doc: Path, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href

    slug = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(str(html_doc))) or ""
    if not slug:
        return href
    return urljoin(slug.rstrip("/") + "/", href.lstrip("/"))


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing: {html_doc}")

        with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
            soup = BeautifulSoup(file, "html.parser")

        entries = soup.select("div.entry")
        if not entries:
            stdlog(f"{GROUP_NAME} - no entries found in {filename}")
            continue

        for entry in entries:
            victim_tag = entry.select_one(".company-name")
            if not victim_tag:
                continue

            victim = victim_tag.get_text(" ", strip=True)
            if not victim:
                continue

            country_tag = entry.select_one(".country-meta .flag-img")
            revenue_tag = entry.select_one(".meta span")
            meta_rows = entry.select(".meta")
            description_tag = entry.select_one(".desc")
            download_tag = entry.select_one("a.download[href]")

            description_parts = []
            if len(meta_rows) > 1:
                for meta_row in meta_rows[1:]:
                    text = meta_row.get_text(" ", strip=True)
                    if text:
                        description_parts.append(text)
            if description_tag:
                description_parts.append(description_tag.get_text(" ", strip=True))

            appender(
                victim=victim,
                group_name=GROUP_NAME,
                description=" | ".join(description_parts),
                website="",
                published="",
                post_url=build_post_url(html_doc, download_tag.get("href", "").strip() if download_tag else ""),
                country=(country_tag.get("alt", "") or "").strip(),
            )


if __name__ == "__main__":
    main()
