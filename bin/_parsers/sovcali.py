"""Parse Sovcali leak entries embedded in the captured blog HTML."""

import datetime
import html
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, extract_md5_from_filename, find_slug_by_md5, errlog, stdlog


GROUP_NAME = "sovcali"
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def parse_published(value: str) -> str:
    try:
        return datetime.datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return ""


def strip_html(value: str) -> str:
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def extract_victim(title: str) -> str:
    """Keep the company portion of a Sovcali post title."""
    return re.split(r"\s+(?:archive|data|files?)\b", title, maxsplit=1, flags=re.IGNORECASE)[0].strip()


POST_PATTERN = re.compile(
    r'id:\s*"(?P<id>[^"]+)".*?'
    r'date:\s*"(?P<date>[^"]+)".*?'
    r'title:\s*"(?P<title>[^"]+)".*?'
    r'excerpt:\s*"(?P<excerpt>.*?)".*?'
    r'specs:\s*\[(?P<specs>.*?)\].*?'
    r'body:\s*`(?P<body>.*?)`',
    re.DOTALL,
)


def main():
    for html_doc in sorted(tmp_dir.glob(f"{GROUP_NAME}-*.html")):
        try:
            content = html_doc.read_text(encoding="utf-8", errors="ignore")
            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(str(html_doc))) or ""
            entries = list(POST_PATTERN.finditer(content))
            if not entries:
                stdlog(f"{GROUP_NAME}: no leak entries found in {html_doc.name}")
                continue

            for entry in entries:
                title = html.unescape(entry["title"]).strip()
                victim = extract_victim(title)
                if not victim:
                    continue

                excerpt = html.unescape(entry["excerpt"]).strip()
                body = strip_html(html.unescape(entry["body"]))
                specs = strip_html(html.unescape(entry["specs"]))
                description = " | ".join(part for part in (excerpt, body, specs) if part)

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    published=parse_published(entry["date"]),
                    post_url=base_url,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME}: parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
