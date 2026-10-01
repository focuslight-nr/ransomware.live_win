import os
import re
from pathlib import Path

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
    group_name = "ulose"
    for html_doc in tmp_dir.glob("ulose-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select("div.grid > div"):
                heading = card.select_one("h3")
                if not heading:
                    continue
                victim = heading.get_text(" ", strip=True)
                if not victim:
                    continue

                domain = re.search(r"(?:^| - )((?:www\.)?[a-z0-9.-]+\.[a-z]{2,})$", victim, re.I)
                website = f"https://{domain.group(1)}" if domain else ""
                details = card.select("div.flex.items-center.justify-between span")
                country = details[0].get_text(" ", strip=True) if details else ""
                if country.lower() in ("korea", "south korea"):
                    country = "KR"
                status = details[-1].get_text(" ", strip=True) if len(details) > 1 else ""

                appender(
                    victim=victim,
                    group_name=group_name,
                    website=website,
                    post_url=slug,
                    country=country,
                    extra_infos={"status": status} if status else {},
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
