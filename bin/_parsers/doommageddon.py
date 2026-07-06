import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

GROUP_NAME = "doommageddon"


def text_or_empty(node):
    return node.get_text(" ", strip=True) if node else ""


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename

        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file.read(), "html.parser")

            cards = soup.select("div.victim-card")
            if not cards:
                continue

            base_url = find_slug_by_md5(GROUP_NAME, extract_md5_from_filename(filename)) or ""
            if base_url:
                base_url = base_url.rstrip("/") + "/"

            for card in cards:
                title_tag = card.find("h2")
                victim = text_or_empty(title_tag)
                if not victim:
                    continue

                status = card.get("data-status", "").strip()
                countdown = text_or_empty(card.select_one("div.countdown"))
                deadline = (card.select_one("div.countdown") or {}).get("data-deadline", "")

                meta_items = [
                    item.get_text(" ", strip=True)
                    for item in card.select("div.card-meta span.meta-item")
                    if item.get_text(" ", strip=True)
                ]

                post_url = ""
                link_tag = card.select_one("a[href]")
                if link_tag and base_url:
                    post_url = urljoin(base_url, link_tag["href"].lstrip("/"))

                description_parts = []
                if status:
                    description_parts.append(f"status: {status}")
                if countdown:
                    description_parts.append(f"countdown: {countdown}")
                if meta_items:
                    description_parts.append(", ".join(meta_items))
                description = " | ".join(description_parts)

                extra_infos = {}
                if deadline:
                    extra_infos["deadline"] = deadline
                if meta_items:
                    if len(meta_items) >= 1:
                        extra_infos["size"] = meta_items[0]
                    if len(meta_items) >= 2:
                        extra_infos["files"] = meta_items[1]

                appender(
                    victim=victim,
                    group_name=GROUP_NAME,
                    description=description,
                    website="",
                    published="",
                    post_url=post_url,
                    country="",
                    extra_infos=extra_infos,
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
