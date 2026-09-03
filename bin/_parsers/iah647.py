#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Parse Cinder (iah647) archive entries from its landing-page table."""

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(dotenv_path=project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv(
    "TMP_DIR", "tmp"
).strip("/")


def post_url(html_doc: Path, href: str) -> str:
    slug = find_slug_by_md5("iah647", extract_md5_from_filename(str(html_doc))) or ""
    return urljoin(slug.rstrip("/") + "/", href) if slug else href


def main():
    group_name = "iah647"

    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        stdlog(f"Parsing: {html_doc}")
        soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")

        for row in soup.select("table.ls.landing tr"):
            cells = row.find_all("td")
            if len(cells) != 4:
                continue

            link = cells[3].find("a", href=True)
            victim = link.get_text(" ", strip=True) if link else cells[3].get_text(" ", strip=True)
            if not victim:
                continue

            size = cells[0].get_text(" ", strip=True)
            status = cells[1].get_text(" ", strip=True)
            hosting = cells[2].get_text(" ", strip=True)
            description = " | ".join(
                part for part in (f"Status: {status}" if status else "", f"Size: {size}" if size else "", f"Hosting: {hosting}" if hosting else "") if part
            )

            appender(
                victim=victim,
                group_name=group_name,
                description=description,
                website="",
                published="",
                post_url=post_url(html_doc, link["href"]) if link else "",
            )


if __name__ == "__main__":
    main()
