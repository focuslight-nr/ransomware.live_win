import os
import re
from datetime import date
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
    group_name = "umbra"
    for html_doc in tmp_dir.glob("umbra-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select("section[data-download-cards] article.download-card"):
                heading = card.select_one("h2")
                victim = heading.get_text(" ", strip=True) if heading else ""
                if not victim:
                    continue

                description = card.select_one(".card-description")
                release = card.select_one(".card-release-date strong")
                release_date = release.get_text(" ", strip=True) if release else ""
                extra_infos = {}
                if release_date:
                    extra_infos["release_date"] = release_date

                footer = card.select_one(".card-updated")
                footer_text = footer.get_text(" ", strip=True) if footer else ""
                updated = re.search(r"Updated on\s+(\d{4}-\d{2}-\d{2})", footer_text, re.I)
                revenue = re.search(r"REVENUE:\s*([^|]+)", footer_text, re.I)
                size = re.search(r"SIZE:\s*([^|]+)", footer_text, re.I)
                if updated:
                    extra_infos["updated"] = updated.group(1)
                if revenue:
                    extra_infos["revenue"] = revenue.group(1).strip()
                if size:
                    extra_infos["size"] = size.group(1).strip()
                if "psa-card" in card.get("class", []) or card.select_one(".psa-tag"):
                    extra_infos["status"] = "PSA"

                published = ""
                if release_date:
                    try:
                        parsed_date = date.fromisoformat(release_date)
                        if parsed_date <= date.today():
                            published = f"{parsed_date.isoformat()} 00:00:00.000000"
                    except ValueError:
                        pass

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description.get_text(" ", strip=True) if description else "",
                    published=published,
                    post_url=slug,
                    website="",
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
