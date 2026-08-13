"""Parse Emperador's ``LEAKS OF SHAME`` listing."""

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, errlog, stdlog


GROUP_NAME = "emperador"
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def parse_deadline(value: str) -> str:
    """Convert the ISO-8601 deadline exposed by a listing card."""
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return ""


def main():
    for html_doc in sorted(tmp_dir.glob(f"{GROUP_NAME}-*.html")):
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(str(html_doc))) or ""
            cards = soup.select("a.card")
            if not cards:
                stdlog(f"{GROUP_NAME}: no leak entries found in {html_doc.name}")
                continue

            for card in cards:
                title = card.select_one(".card-title")
                victim = title.get_text(" ", strip=True) if title else ""
                if not victim:
                    continue

                description_tag = card.select_one(".card-desc")
                description = description_tag.get_text(" ", strip=True) if description_tag else ""
                timer = card.select_one(".timer")
                deadline = parse_deadline(timer.get("data-end", "")) if timer else ""
                status = "published" if timer and "released-status" in (timer.get("class") or []) else "pending publication"
                if deadline:
                    description = f"{description} | Publication deadline: {deadline}" if description else f"Publication deadline: {deadline}"
                description = f"{description} | Status: {status}" if description else f"Status: {status}"

                post_url = urljoin(base_url, card.get("href", "")) if base_url else card.get("href", "")
                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    published=deadline,
                    post_url=post_url,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME}: parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
