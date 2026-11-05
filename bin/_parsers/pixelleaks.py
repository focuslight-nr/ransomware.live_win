import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group_name = "pixelleaks"
    for html_doc in tmp_dir.glob("pixelleaks-*.html"):
        try:
            stdlog(f"Parsing: {html_doc}")
            slug = find_slug_by_md5(group_name, extract_md5_from_filename(html_doc.name))
            if not slug:
                errlog(f"{group_name} - no location found for {html_doc.name}")
                continue
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select("#lgtab-exposures article.lg-entry"):
                heading = card.select_one(".lg-name")
                victim = heading.get_text(" ", strip=True) if heading else ""
                if not victim or victim.lower() == "unnamed":
                    continue
                status = card.select_one(".lg-entry-head .stamp")
                summary = card.select_one(".lgm-summary")
                extra = {}
                if status:
                    extra["status"] = status.get_text(" ", strip=True)
                if summary:
                    extra["description"] = summary.get_text(" ", strip=True)
                appender(victim=victim, group_name=group_name, post_url=slug, extra_infos=extra)
        except Exception as exc:
            errlog(f"{group_name} - parsing failed for {html_doc.name}: {exc}")


if __name__ == "__main__":
    main()
