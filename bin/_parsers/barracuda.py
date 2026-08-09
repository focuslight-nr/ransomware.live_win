"""Parse Barracuda auction listings captured by the scraper."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, errlog, stdlog


GROUP_NAME = "barracuda"
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def timestamp_to_utc(value: str) -> str:
    """Convert the page's millisecond timestamp to the appender date format."""
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    except (TypeError, ValueError, OSError):
        return ""


def extract_website(description: str) -> str:
    match = re.search(r"(?i)\b(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?:/[^\s\])}]*)?", description)
    return match.group(1).rstrip(".,;") if match else ""


def main():
    for html_doc in sorted(tmp_dir.glob(f"{GROUP_NAME}-*.html")):
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(str(html_doc))) or ""

            entries = soup.select("article.lot")
            if not entries:
                stdlog(f"{GROUP_NAME}: no auction entries found in {html_doc.name}")
                continue

            for entry in entries:
                victim_tag = entry.select_one("h3")
                victim = victim_tag.get_text(" ", strip=True) if victim_tag else ""
                if not victim:
                    continue

                description_tag = entry.select_one("p.desc")
                description = description_tag.get_text(" ", strip=True) if description_tag else ""
                size_tag = next(
                    (node.parent for node in entry.select(".meta span") if node.get_text(" ", strip=True).lower() == "size"),
                    None,
                )
                if size_tag:
                    size = size_tag.get_text(" ", strip=True).removeprefix("Size").strip()
                    if size:
                        description = f"{description} | Size: {size}" if description else f"Size: {size}"

                status = (entry.get("data-status") or "").strip()
                sale_date = timestamp_to_utc(entry.get("data-sale", ""))
                if status:
                    description = f"{description} | Status: {status}" if description else f"Status: {status}"

                action = entry.select_one("a.action-link[href]")
                post_url = action["href"].strip() if action else base_url
                if post_url and base_url:
                    post_url = urljoin(base_url, post_url)

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    website=extract_website(description),
                    published=sale_date,
                    post_url=post_url,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME}: parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
