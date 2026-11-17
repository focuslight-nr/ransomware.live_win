import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


root = Path(__file__).resolve().parent.parent.parent
load_dotenv(root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group = "inception"
    for path in tmp_dir.glob("inception-*.html"):
        try:
            stdlog(f"Parsing: {path}")
            slug = find_slug_by_md5(group, extract_md5_from_filename(path.name))
            if not slug:
                errlog(f"{group} - no location found for {path.name}")
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for entry in soup.select("main details.entry"):
                name = entry.select_one("summary .entry-name")
                if not name:
                    continue
                victim = name.get_text(" ", strip=True)
                if not victim:
                    continue
                description = entry.select_one(".detail-desc")
                appender(
                    victim=victim,
                    group_name=group,
                    description=description.get_text(" ", strip=True) if description else "",
                    post_url=slug,
                )
        except Exception as exc:
            errlog(f"{group} - parsing failed for {path.name}: {exc}")


if __name__ == "__main__":
    main()
