import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


root = Path(__file__).resolve().parent.parent.parent
load_dotenv(root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group = "climax inc"
    for path in tmp_dir.glob("climaxinc-*.html"):
        try:
            stdlog(f"Parsing: {path}")
            slug = find_slug_by_md5(group, extract_md5_from_filename(path.name))
            if not slug:
                errlog(f"{group} - no location found for {path.name}")
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for article in soup.select("article.post"):
                name = article.get("data-title", "").strip()
                link = article.select_one("h2.post-title a[href]")
                if not name or not link or name.lower() == "redacted":
                    continue
                website_link = article.select_one('p.post-meta a[href^="http"]')
                date = article.select_one("time[datetime]")
                appender(
                    victim=name,
                    group_name=group,
                    website=website_link["href"] if website_link else "",
                    post_url=urljoin(slug, link["href"]),
                    published=date["datetime"] if date else "",
                )
        except Exception as exc:
            errlog(f"{group} - parsing failed for {path.name}: {exc}")


if __name__ == "__main__":
    main()
