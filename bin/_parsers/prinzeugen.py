"""
    Parser for Prinz Eugen
"""

import datetime
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

target_group_name = "prinzeugen"


def normalize_website(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://", "", value, flags=re.I)
    return value.rstrip("/")


def build_post_url(filename: str, href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href

    slug = find_slug_by_md5(target_group_name, extract_md5_from_filename(filename))
    if not slug:
        return href
    return urljoin(slug.rstrip("/") + "/", href.lstrip("/"))


def extract_website_and_description(raw_description: str) -> tuple[str, str]:
    parts = [part.strip() for part in raw_description.splitlines() if part.strip()]
    if not parts:
        return "", ""

    website = ""
    description_parts = []
    for index, part in enumerate(parts):
        if index == 0 and re.fullmatch(r"(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/.*)?", part):
            website = normalize_website(part)
            continue
        description_parts.append(part)

    return website, " | ".join(description_parts)


def parse_published(date_str: str) -> str:
    if not date_str:
        return ""

    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            continue
    return date_str


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{target_group_name}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing: {html_doc}")
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            sections = soup.select("a.landing-shell--portal")
            for section in sections:
                try:
                    name_tag = section.select_one("h2.landing-portal-frame__name")
                    victim = name_tag.get_text(" ", strip=True) if name_tag else ""
                    if not victim or "NOT A CASE FILE" in victim.upper():
                        continue

                    desc_tag = section.select_one("p.landing-portal-frame__desc")
                    raw_description = desc_tag.get_text("\n", strip=True) if desc_tag else ""
                    website, description = extract_website_and_description(raw_description)

                    date_tag = section.select_one(".landing-portal-frame__footer span")
                    published = parse_published(date_tag.get_text(" ", strip=True) if date_tag else "")

                    post_url = build_post_url(filename, section.get("href", ""))

                    appender(
                        victim=victim,
                        group_name=target_group_name,
                        description=description,
                        website=website,
                        published=published,
                        post_url=post_url,
                    )
                except Exception as exc:
                    errlog(f"{target_group_name} - error parsing item: {exc}")
        except Exception as exc:
            errlog(f"{target_group_name} - error reading file {filename}: {exc}")


if __name__ == "__main__":
    main()
