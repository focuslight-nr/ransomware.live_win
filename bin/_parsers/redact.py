"""
    Parser for REDACT leak listings
"""

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

GROUP_NAME = "redact"


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename

        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            rows = soup.select("tbody tr")
            if not rows:
                continue

            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(filename)) or ""
            post_url = urljoin(base_url.rstrip("/") + "/", "companies") if base_url else ""

            for row in rows:
                if "view-all-row" in (row.get("class") or []):
                    continue

                cells = row.find_all("td")
                if len(cells) < 6:
                    continue

                victim = cells[0].get_text(" ", strip=True)
                if not victim:
                    continue

                extra_infos = {}
                revenue = cells[1].get_text(" ", strip=True)
                sector = cells[2].get_text(" ", strip=True)
                stock_ticker = cells[3].get_text(" ", strip=True)
                data_size = cells[4].get_text(" ", strip=True)
                file_count = cells[5].get_text(" ", strip=True)

                if revenue:
                    extra_infos["revenue"] = revenue
                if sector:
                    extra_infos["sector"] = sector
                if stock_ticker:
                    extra_infos["stock_ticker"] = stock_ticker
                if data_size:
                    extra_infos["data_size"] = data_size
                if file_count:
                    extra_infos["file_count"] = file_count

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description="",
                    website="",
                    published="",
                    post_url=post_url,
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
