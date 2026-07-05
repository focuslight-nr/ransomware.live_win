import os
import re
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

GROUP_NAME = "wallstreet"


def extract_country(card):
    for class_name in card.get("class") or []:
        if class_name.startswith("fi-") and len(class_name) == 5:
            return class_name.split("-", 1)[1].upper()
    return ""


def extract_website(description):
    match = re.search(r"\b(?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}\b", description, re.I)
    if not match:
        return ""
    website = match.group(0).rstrip(").,")
    return website if website.startswith(("http://", "https://")) else website.lower()


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename

        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file.read(), "html.parser")

            cards = soup.find_all("div", class_=lambda c: c and "_card_" in c)
            if not cards:
                continue

            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(filename)) or ""
            post_url = urljoin(base_url.rstrip("/") + "/", "") if base_url else ""

            for card in cards:
                title_tag = card.find("h2")
                if not title_tag:
                    continue

                victim = title_tag.get_text(" ", strip=True)
                if not victim:
                    continue

                description_tag = card.find("p")
                description = description_tag.get_text(" ", strip=True) if description_tag else ""
                timer_tag = card.find("span", class_=lambda c: c and "_timerValue_" in c)
                timer_value = timer_tag.get_text(" ", strip=True) if timer_tag else ""

                exposure_parts = [
                    span.get_text(" ", strip=True)
                    for span in card.find_all("span", class_=lambda c: c and ("_stat_" in c or "_more_" in c))
                    if span.get_text(" ", strip=True)
                ]

                extra_infos = {}
                if timer_value:
                    extra_infos["countdown"] = timer_value
                if exposure_parts:
                    extra_infos["exposure"] = ", ".join(exposure_parts)

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    website=extract_website(description),
                    published="",
                    post_url=post_url,
                    country=extract_country(card),
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
