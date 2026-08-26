import datetime
import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
load_dotenv(home / ".env")

tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", ".")) / os.getenv(
    "TMP_DIR", "tmp"
).strip("/")
base_url = "http://4zrjdyuq4sjogm2epwwoleegquavhwo3o7fakstnlgox6guqt3qpe4qd.onion"


def parse_published(value):
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
    except (TypeError, ValueError):
        return ""


def main():
    group_name = Path(__file__).stem

    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8"), "html.parser")

            for post in soup.select("article.post-item"):
                link = post.select_one("h4.post-item-title a[href]")
                if not link:
                    continue

                victim = link.get_text(" ", strip=True)
                if not victim:
                    continue

                published_tag = post.select_one("time[datetime]")
                appender(
                    victim=victim,
                    group_name=group_name,
                    description="",
                    website=victim,
                    published=parse_published(
                        published_tag.get("datetime", "") if published_tag else ""
                    ),
                    post_url=urljoin(base_url, link["href"]),
                    country="",
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing fail with error: {exc} in file: {html_doc.name}")


if __name__ == "__main__":
    main()
