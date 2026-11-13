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
    group = "vortex"
    for path in tmp_dir.glob("vortex-*.html"):
        try:
            stdlog(f"Parsing: {path}")
            slug = find_slug_by_md5(group, extract_md5_from_filename(path.name))
            if not slug:
                errlog(f"{group} - no location found for {path.name}")
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select(".publications .card"):
                link = card.select_one("h3 a.card-link[href]")
                if not link:
                    continue
                name = link.get_text(" ", strip=True)
                if not name:
                    continue
                date = card.select_one("time")
                appender(
                    victim=name,
                    group_name=group,
                    post_url=urljoin(slug, link["href"]),
                    published=date.get_text(strip=True) if date else "",
                )
        except Exception as exc:
            errlog(f"{group} - parsing failed for {path.name}: {exc}")


if __name__ == "__main__":
    main()
