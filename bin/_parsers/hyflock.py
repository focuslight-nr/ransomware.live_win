import os
import re
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
    group_name = "hyflock"
    for html_doc in tmp_dir.glob("hyflock-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select("article.leak-card"):
                company_el = card.select_one(".leak-card-company")
                title_el = card.select_one(".leak-card-title")

                victim = ""
                if company_el:
                    company_text = company_el.get_text(" ", strip=True)
                    if "█" not in company_text:
                        victim = company_text

                if not victim and title_el:
                    victim = title_el.get_text(" ", strip=True)

                if not victim:
                    continue

                desc_el = card.select_one(".leak-card-desc")
                description = desc_el.get_text(" ", strip=True) if desc_el else ""

                date_el = card.select_one(".leak-card-date")
                published = ""
                if date_el:
                    date_text = date_el.get_text(" ", strip=True)
                    try:
                        dt_obj = datetime.strptime(date_text, "%b %d, %Y")
                        published = dt_obj.strftime("%Y-%m-%d 00:00:00.000000")
                    except ValueError:
                        published = ""

                post_url = slug
                onclick_attr = card.get("onclick", "")
                if onclick_attr:
                    match = re.search(r"window\.location\.href=['\"](/blog/view/[^'\"]+)['\"]", onclick_attr)
                    if match:
                        path = match.group(1)
                        post_url = urljoin(slug, path)

                website = ""
                if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", victim, re.I):
                    website = f"https://{victim}"

                extra_infos = {}
                status_el = card.select_one(".leak-card-status")
                if status_el:
                    extra_infos["status"] = status_el.get_text(" ", strip=True)

                size_el = card.select_one(".leak-card-size")
                if size_el:
                    extra_infos["size"] = size_el.get_text(" ", strip=True)

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    published=published,
                    post_url=post_url,
                    website=website,
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
