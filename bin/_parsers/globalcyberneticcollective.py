import os
from datetime import datetime
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
    group_name = "global cybernetic collective"
    for html_doc in tmp_dir.glob("globalcyberneticcollective-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select(".card[data-target]"):
                title = card.select_one(".card-body .card-title")
                victim = title.get_text(" ", strip=True) if title else ""
                if not victim or card.get("data-target") == "target-0":
                    continue

                site = card.select_one(".card-meta a[href]")
                website = site["href"].strip() if site else ""
                if not website.startswith(("http://", "https://")):
                    website = ""

                description = card.select_one(".card-desc")
                date = card.select_one(".card-footer > div")
                published = ""
                if date:
                    try:
                        published = datetime.strptime(
                            date.get_text(" ", strip=True).replace("Sept ", "Sep "),
                            "%d %b %Y",
                        ).strftime("%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        published = date.get_text(" ", strip=True)

                link = card.select_one(".card-footer a[href]")
                post_url = urljoin(slug + "/", link["href"]) if link else slug
                extra_infos = {}
                for detail in card.select(".card-meta > div"):
                    label, separator, value = detail.get_text(" ", strip=True).partition(":")
                    if separator and label in ("Address", "Archive size"):
                        extra_infos[label] = value.strip()

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description.get_text(" ", strip=True) if description else "",
                    website=website,
                    published=published,
                    post_url=post_url,
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
