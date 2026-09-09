import os
from pathlib import Path

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
    group_name = "shiba"
    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            seen = set()
            for heading in soup.find_all(
                "h1", class_=lambda classes: classes and "text-[2rem]" in classes
            ):
                victim = heading.get_text(" ", strip=True)
                if not victim or victim in seen:
                    continue
                seen.add(victim)

                container = heading.parent
                details = [
                    paragraph.get_text(" ", strip=True)
                    for paragraph in container.find_all("p", recursive=False)
                ]
                website = ""
                link = container.find("a", href=True)
                if link and link["href"].startswith(("http://", "https://")):
                    website = link["href"]

                appender(
                    victim,
                    group_name,
                    "\n".join(details),
                    website,
                    "",
                    find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))),
                    "",
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
