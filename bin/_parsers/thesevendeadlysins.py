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
    group_name = "the seven deadly sins"
    for html_doc in tmp_dir.glob("thesevendeadlysins-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue

            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            cards = soup.select("article.leak-card")
            if not cards:
                errlog(f"{group_name} - no victim cards found in {html_doc.name}")
                continue

            for card in cards:
                title = card.select_one("h3 a")
                if not title:
                    continue
                victim = title.get_text(" ", strip=True)
                if not victim:
                    continue

                desc = card.select_one(".company-desc")
                site = card.select_one(".site-url a[href]")
                href = title.get("href", "")
                post_url = urljoin(slug, href) if href else slug
                extra_infos = {}
                status = card.select_one(".contact-note")
                if status:
                    extra_infos["status"] = status.get_text(" ", strip=True)
                affected = card.select_one(".affected")
                if affected:
                    extra_infos["affected"] = affected.get_text(" ", strip=True)
                for term in card.select(".leak-impact div"):
                    label = term.select_one("dt")
                    value = term.select_one("dd")
                    if label and value and label.get_text(" ", strip=True) == "Rows exfiltrated":
                        extra_infos["rows exfiltrated"] = value.get_text(" ", strip=True)
                        break

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=desc.get_text(" ", strip=True) if desc else "",
                    published="",
                    post_url=post_url,
                    website=site.get("href", "") if site else "",
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
