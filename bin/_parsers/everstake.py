import os
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
    group_name = "everstake"
    for html_doc in tmp_dir.glob("everstake-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for row in soup.select("section.announcement-group tr[data-announcement-id]"):
                title = row.select_one("td.column-title a[href]")
                if not title or title.select_one(".blurred-fragment"):
                    continue
                victim = title.get_text(" ", strip=True)
                if not victim or "Hidden name" in victim:
                    continue
                post_url = urljoin(slug + "/", title["href"])
                category = row.select_one("td.column-category")
                size = row.select_one("td.column-size")
                status = row.select_one("td.column-status")
                extra_infos = {}
                for key, node in (("category", category), ("size", size), ("status", status)):
                    if node:
                        extra_infos[key] = node.get_text(" ", strip=True)
                appender(
                    victim=victim,
                    group_name=group_name,
                    website=f"https://{victim}" if "." in victim and " " not in victim else "",
                    post_url=post_url,
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
