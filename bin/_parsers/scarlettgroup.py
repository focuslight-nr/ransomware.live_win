import os
import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv(
    "TMP_DIR", "tmp"
).strip("/")


def main():
    group_name = "scarlettgroup"
    for html_doc in tmp_dir.glob("scarlettgroup-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select("main .grid a.card"):
                heading = card.select_one("h3.card__domain")
                victim = heading.get_text(" ", strip=True) if heading else ""
                if not victim:
                    continue

                description = card.select_one(".card__text")
                date_text = card.select_one(".card__foot .stat:last-child span")
                date_value = date_text.get_text(" ", strip=True) if date_text else ""
                published = f"{date_value} 00:00:00.000000" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value) else ""
                href = card.get("href", "")
                website = f"https://{victim}" if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", victim, re.I) else ""

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description.get_text(" ", strip=True) if description else "",
                    published=published,
                    post_url=urljoin(slug, href) if href else slug,
                    website=website,
                    country="",
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
