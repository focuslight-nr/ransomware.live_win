"""
    Parser for UnSafe leak listings
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |           |     X    |
    +-----------------------+-----------+----------+
"""

import os
import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import (
    appender,
    errlog,
    extract_md5_from_filename,
    find_slug_by_md5,
    stdlog,
)


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def normalize_website(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    value = re.sub(r"^https?://", "", value, flags=re.I)
    return value.rstrip("/")


def build_post_url(group_name: str, html_doc: Path, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href

    slug = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc)))
    if not slug:
        return href
    return urljoin(slug.rstrip("/") + "/", href.lstrip("/"))


def main():
    group_name = Path(__file__).stem

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{group_name}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            reels = soup.select("a.reel-link")
            if not reels:
                stdlog(f"{group_name} - no reel-link entries found in {filename}")
                continue

            for reel_link in reels:
                reel = reel_link.select_one(".reel") or reel_link
                name_tag = reel.select_one("h3")
                victim = name_tag.get_text(" ", strip=True) if name_tag else ""
                if not victim:
                    continue

                paragraphs = [p.get_text(" ", strip=True) for p in reel.select(".reel-left p")]
                website = ""
                description_parts = []
                for line in paragraphs:
                    if not line:
                        continue
                    if re.search(r"(https?://|www\.|[A-Za-z0-9.-]+\.[A-Za-z]{2,})", line) and not website:
                        website = normalize_website(line.split(":", 1)[-1].strip())
                        continue
                    description_parts.append(line)

                description = " | ".join(description_parts)
                post_url = build_post_url(group_name, html_doc, reel_link.get("href", "").strip())
                appender(victim, group_name, description=description, website=website, post_url=post_url)
        except Exception as exc:
            errlog(f"{group_name} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
