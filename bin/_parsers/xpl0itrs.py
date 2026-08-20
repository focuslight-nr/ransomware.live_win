"""Parse victim listings published by xpl0itrs."""

import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, errlog


def main():
    home = Path(__file__).resolve().parents[2]
    tmp_dir = home / os.getenv("TMP_DIR", "tmp").strip("/")

    for html_doc in tmp_dir.glob("xpl0itrs-*.html"):
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            base_url = find_slug_by_md5("xpl0itrs", extract_md5_from_filename(str(html_doc)))

            # The first listing table contains disclosed victims.  The later
            # `static-rows` table is an initial-access marketplace, not a
            # victim list, so it is deliberately excluded.
            table = soup.select_one("table.listing-table:not(.static-rows)")
            if not table:
                errlog(f"xpl0itrs - no victim listing table found in {html_doc.name}")
                continue

            for row in table.select("tbody tr"):
                link = row.select_one("a.row-link")
                name = row.select_one(".row-name")
                if not link or not name:
                    continue
                victim = name.get_text(" ", strip=True)
                if not victim or not re.search(r"[A-Za-z0-9]", victim):
                    continue
                description = " ".join(
                    element.get_text(" ", strip=True)
                    for element in row.select(".row-tagline, .row-sector, .row-data")
                    if element.get_text(" ", strip=True)
                )
                appender(
                    victim=victim,
                    group_name="xpl0itrs",
                    description=description,
                    website="",
                    published="",
                    post_url=base_url + link.get("href", ""),
                    country="",
                )
        except Exception as exc:
            errlog(f"xpl0itrs - parsing fail with error: {exc} in file: {html_doc.name}")
