"""Parse Helix's rendered disclosure feed."""

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
load_dotenv(dotenv_path=home / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", ".")) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith("helix-"):
            continue

        html_path = tmp_dir / filename
        try:
            soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            md5_value = extract_md5_from_filename(str(html_path))
            base_url = find_slug_by_md5("helix", md5_value) or ""

            for feed in soup.select("a.feed"):
                title = feed.select_one(".feed-top h3")
                if not title:
                    continue
                victim = title.get_text(" ", strip=True)
                if not victim:
                    continue

                description = ""
                summary = feed.select_one("p")
                if summary:
                    description = summary.get_text(" ", strip=True)

                post_url = feed.get("href", "").strip()
                if post_url and base_url:
                    post_url = urljoin(base_url, post_url)

                appender(victim, "helix", description, "", "", post_url, "")
        except Exception as exc:
            errlog(f"helix - parsing failed for {filename}: {exc}")


if __name__ == "__main__":
    main()
