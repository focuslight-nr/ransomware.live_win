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
    group_name = "n0n"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            soup = BeautifulSoup(
                html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser"
            )
            seen = set()
            for card in soup.select(".pane .card"):
                name = card.select_one(".vname")
                if not name:
                    continue
                victim = name.get_text(" ", strip=True)
                if not victim or victim in seen:
                    continue
                seen.add(victim)

                description_parts = []
                meta = card.select_one(".meta")
                if meta:
                    description_parts.append(meta.get_text(" ", strip=True))
                detail_link = card.find("a", href=True)
                if detail_link and detail_link["href"].startswith("#v-"):
                    detail = soup.select_one(detail_link["href"])
                    if detail:
                        summary = detail.select_one(".summary")
                        if summary:
                            description_parts.append(summary.get_text(" ", strip=True))

                appender(victim, group_name, "\n".join(description_parts))
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
