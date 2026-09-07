import os
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv(
    "TMP_DIR", "tmp"
).strip("/")


def main():
    group_name = "vexy"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for item in soup.select(".target-box"):
                name = item.select_one(".company-name")
                if not name:
                    continue
                details = [detail.get_text(" ", strip=True) for detail in item.select(".detail-item")]
                website = next((detail for detail in details if "." in detail), "")
                description = item.select_one(".description-text")
                date = item.select_one(".date-row")
                published = ""
                if date:
                    try:
                        published = datetime.strptime(
                            date.get_text(" ", strip=True), "%Y-%m-%d %H:%M:%S UTC"
                        ).strftime("%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        published = date.get_text(" ", strip=True)
                appender(
                    name.get_text(" ", strip=True),
                    group_name,
                    description.get_text(" ", strip=True) if description else "",
                    website,
                    published,
                    item.get("data-link", ""),
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
