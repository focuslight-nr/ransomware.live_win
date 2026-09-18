import os
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
    group_name = "cinder"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for item in soup.select("table.ls.landing tr"):
                name = item.select_one("td:last-child a")
                if not name:
                    continue
                details = item.select("td")
                description = " ".join(
                    detail.get_text(" ", strip=True) for detail in details[:-1]
                )
                appender(name.get_text(" ", strip=True), group_name, description)
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
