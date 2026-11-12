import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


root = Path(__file__).resolve().parent.parent.parent
load_dotenv(root / ".env")
tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", str(root))) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group = "curious worm"
    for path in tmp_dir.glob("curiousworm-*.html"):
        try:
            stdlog(f"Parsing: {path}")
            slug = find_slug_by_md5(group, extract_md5_from_filename(path.name))
            if not slug:
                errlog(f"{group} - no location found for {path.name}")
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            for card in soup.select(".target-card"):
                fields = {}
                for field in card.select(".field"):
                    label = field.select_one(".label")
                    value = field.select_one(".value")
                    if label and value:
                        fields[label.get_text("", strip=True).rstrip(":").lower()] = value.get_text("", strip=True)
                name = fields.get("company", "").strip()
                if not name or "*" in name:
                    continue
                website = name if name.startswith(("http://", "https://")) else ""
                if not website and "." in name and " " not in name:
                    website = "https://" + name
                appender(victim=name, group_name=group, website=website, post_url=slug,
                         extra_infos={k: v for k, v in fields.items() if k != "company" and v})
        except Exception as exc:
            errlog(f"{group} - parsing failed for {path.name}: {exc}")


if __name__ == "__main__":
    main()
