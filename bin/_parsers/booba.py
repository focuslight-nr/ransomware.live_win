"""
    Parser for Booba leak listings
"""

import datetime
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, stdlog


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

GROUP_NAME = "booba"


def normalize_website(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://", "", value, flags=re.I)
    return value.rstrip("/")


def parse_published(raw_value: str) -> str:
    if not raw_value:
        return ""

    raw_value = raw_value.strip()
    try:
        dt = datetime.datetime.fromisoformat(raw_value)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return raw_value


def parse_published_from_tag(time_tag) -> str:
    if not time_tag:
        return ""

    datetime_attr = (time_tag.get("datetime") or "").strip()
    display_text = time_tag.get_text(" ", strip=True)

    # Some pages split the date between visible text and a time-only datetime attr.
    if datetime_attr and re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2})?", datetime_attr):
        cleaned_text = re.sub(r"\s+,", ",", display_text)
        combined = f"{cleaned_text}:00" if re.fullmatch(r".*\d{2}:\d{2}$", cleaned_text) else cleaned_text
        for fmt in ("%b %d, %Y, %H:%M:%S", "%b %d, %Y, %H:%M"):
            try:
                dt = datetime.datetime.strptime(combined, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                continue

    published = parse_published(datetime_attr)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", published):
        return published

    cleaned_text = re.sub(r"\s+,", ",", display_text)
    for fmt in ("%b %d, %Y, %H:%M", "%b %d, %Y, %H:%M:%S"):
        try:
            dt = datetime.datetime.strptime(cleaned_text, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            continue

    return published if published != datetime_attr else ""


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing: {html_doc}")

        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            entries = soup.select("main > div.py-6")
            if not entries:
                stdlog(f"{GROUP_NAME} - no listing entries found in {filename}")
                continue

            for entry in entries:
                victim_tag = entry.select_one("h2")
                victim = victim_tag.get_text(" ", strip=True) if victim_tag else ""
                if not victim or victim.lower() == "about us":
                    continue

                published_tag = entry.select_one("time")
                published = parse_published_from_tag(published_tag)

                website = ""
                description_parts = []
                for paragraph in entry.select(".parsed-post-text p"):
                    text = paragraph.get_text(" ", strip=True)
                    if not text:
                        continue

                    if text.lower().startswith("website:"):
                        website_link = paragraph.select_one("a[href]")
                        website_value = (
                            website_link.get_text(" ", strip=True)
                            if website_link
                            else text.split(":", 1)[-1].strip()
                        )
                        website = normalize_website(website_value)
                        continue

                    description_parts.append(text)

                description = " | ".join(description_parts)

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    website=website,
                    published=published,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
