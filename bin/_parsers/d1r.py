import os
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import (
    appender,
    extract_md5_from_filename,
    find_slug_by_md5,
    stdlog,
)


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = Path(os.getenv("RANSOMWARELIVE_HOME", str(project_root)))
if not home_env.is_absolute():
    home_env = project_root / home_env
tmp_dir = home_env / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group_name = "d1r"
    stdlog(f"Processing group: {group_name}")

    for html_doc in sorted(tmp_dir.glob(f"{group_name}-*.html")):
        stdlog(f"Parsing: {html_doc}")
        with html_doc.open("r", encoding="utf-8", errors="ignore") as handle:
            soup = BeautifulSoup(handle, "html.parser")

        base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
        base_url = base_url.rstrip("/")
        listing_url = f"{base_url}/items/" if base_url else ""

        seen_victims = set()
        for card in soup.select("div.product-card.live-card"):
            victim = (card.get("data-title") or "").strip()
            if not victim or victim in seen_victims:
                continue

            product_id = (card.get("data-product_id") or "").strip()
            tags = [
                tag.get_text(" ", strip=True).lstrip("•").strip()
                for tag in card.select(".product-tags .product-tag")
            ]
            tags = [tag for tag in tags if tag]

            timer = ""
            timer_node = card.select_one(".product-page-product-timer")
            if timer_node:
                timer = timer_node.get_text(" ", strip=True)

            description_parts = []
            if tags:
                description_parts.append(f"Tags: {', '.join(tags)}")
            if timer:
                description_parts.append(timer)
            description = "\n".join(description_parts)

            post_url = listing_url
            if listing_url and product_id:
                post_url = f"{listing_url}#product-{product_id}"

            appender(
                victim=victim,
                group_name=group_name,
                description=description,
                website="",
                published="",
                post_url=post_url,
                country="",
                extra_infos={"product_id": product_id},
            )
            seen_victims.add(victim)


if __name__ == "__main__":
    main()
