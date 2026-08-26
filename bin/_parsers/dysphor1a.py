import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
load_dotenv(home / ".env")

tmp_dir = Path(os.getenv("RANSOMWARELIVE_HOME", ".")) / os.getenv(
    "TMP_DIR", "tmp"
).strip("/")


def card_field(card, label):
    for field in card.select("span"):
        if field.get_text(" ", strip=True).lower() != label.lower():
            continue
        value = field.find_next_sibling("span")
        if value:
            return value.get_text(" ", strip=True)
    return ""


def main():
    group_name = Path(__file__).stem

    for html_doc in tmp_dir.glob(f"{group_name}-*.html"):
        try:
            soup = BeautifulSoup(html_doc.read_text(encoding="utf-8"), "html.parser")

            for card in soup.select("article.corner-brackets"):
                title = card.find("h3")
                if not title:
                    continue

                victim = title.get_text(" ", strip=True)
                description = ""
                for paragraph in card.find_all("p"):
                    text = paragraph.get_text(" ", strip=True)
                    if text and text != victim and "Auction timer" not in text:
                        description = text
                        break

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website="",
                    published="",
                    post_url="",
                    country=card_field(card, "Country"),
                )
        except Exception as exc:
            errlog(f"{group_name} - parsing fail with error: {exc} in file: {html_doc.name}")


if __name__ == "__main__":
    main()
