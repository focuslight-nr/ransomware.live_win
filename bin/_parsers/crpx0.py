#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser for CRPxO leak listings.
Extracts victims from the public feed cards available in saved HTML.
"""

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, stdlog


script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

GROUP_NAME = "crpx0"
BASE_URL = "https://crpx0.su/"


def parse_card(card):
    victim_tag = card.select_one(".card-header-info h3")
    victim = victim_tag.get_text(" ", strip=True) if victim_tag else ""
    if not victim:
        return None

    status_tag = card.select_one(".badge")
    status = status_tag.get_text(" ", strip=True) if status_tag else ""

    info_items = card.select("div[style*='display:flex'] > div")
    location = info_items[0].get_text(" ", strip=True) if len(info_items) > 0 else ""
    industry = info_items[1].get_text(" ", strip=True) if len(info_items) > 1 else ""
    data_size = info_items[2].get_text(" ", strip=True) if len(info_items) > 2 else ""

    country = ""
    if "," in location:
        country = location.split(",")[-1].strip()
    elif location:
        country = location

    detail_link = card.select_one("a[href]")
    post_url = urljoin(BASE_URL, detail_link["href"]) if detail_link and detail_link.get("href") else ""

    description_parts = [part for part in (location, industry, data_size, status) if part]
    description = " | ".join(description_parts)
    extra_infos = {
        "location": location,
        "industry": industry,
        "data_size": data_size,
        "status": status,
    }

    return {
        "victim": victim,
        "description": description,
        "country": country,
        "post_url": post_url,
        "extra_infos": extra_infos,
    }


def main():
    for filename in os.listdir(tmp_dir):
        if not filename.startswith(f"{GROUP_NAME}-") or not filename.endswith(".html"):
            continue

        html_doc = tmp_dir / filename
        stdlog(f"Parsing {GROUP_NAME}: {html_doc}")

        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            cards = soup.select("div.victim-grid div.victim-card")
            if not cards:
                stdlog(f"{GROUP_NAME} - no victim cards found in {filename}")
                continue

            for card in cards:
                parsed = parse_card(card)
                if not parsed:
                    continue

                appender(
                    victim=parsed["victim"],
                    group_name=GROUP_NAME,
                    description=parsed["description"],
                    published="",
                    post_url=parsed["post_url"],
                    country=parsed["country"],
                    extra_infos=parsed["extra_infos"],
                )
        except Exception as exc:
            errlog(f"{GROUP_NAME} - parsing fail with error: {exc} in file:{filename}")


if __name__ == "__main__":
    main()
