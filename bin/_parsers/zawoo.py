"""Parser for ZaWoo's static victim listing."""

import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, stdlog


load_dotenv(dotenv_path=Path("../.env"))
home = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home + os.getenv("TMP_DIR", "/tmp/"))


def main():
    group_name = "zawoo"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        stdlog(f"Parsing: {html_doc}")
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8"), "html.parser")
            for card in soup.select("#grid .pCard"):
                title = card.select_one(".pTitle")
                status = card.select_one(".pStatus")
                country = card.select_one(".pCountryTop")
                description = card.select_one(".pDetail")

                victim = title.get_text(" ", strip=True) if title else ""
                if not victim or victim.lower().startswith("company id"):
                    continue
                if not status or "published" not in status.get("class", []):
                    continue

                country_value = ""
                if country:
                    country_value = country.get_text(" ", strip=True)
                    if country_value.lower().startswith("country:"):
                        country_value = country_value.split(":", 1)[1].strip()

                appender(
                    victim,
                    group_name,
                    description.get_text(" ", strip=True) if description else "",
                    "",
                    "",
                    "",
                    country_value,
                )
        except Exception as error:
            errlog(f"{group_name} - error reading {html_doc}: {error}")


if __name__ == "__main__":
    main()
