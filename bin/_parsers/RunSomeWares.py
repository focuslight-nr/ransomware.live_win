"""Parser for Run Some Wares victim cards."""

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, stdlog


load_dotenv(dotenv_path=Path("../.env"))
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))


def main():
    group_name = "runsomewares"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        stdlog(f"Parsing: {html_doc}")
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8"), "html.parser")
            for card in soup.select(".card"):
                title = card.select_one(".card-title")
                if not title:
                    continue
                victim = title.get_text(" ", strip=True)
                if not victim:
                    continue

                description = card.select_one(".card-text")
                link = card.select_one("a.more-info-link[href]")
                post_url = urljoin(
                    "http://rnsmwareartse3m4hjsumjf222pnka6gad26cqxqmbjvevhbnym5p6ad.onion/",
                    link["href"],
                ) if link else ""
                appender(
                    victim,
                    group_name,
                    description.get_text(" ", strip=True) if description else "",
                    "",
                    "",
                    post_url,
                )
        except Exception as error:
            errlog(f"{group_name} - error reading {html_doc}: {error}")


if __name__ == "__main__":
    main()
