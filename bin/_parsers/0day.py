#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def main():
    group_name = "0day"
    stdlog(f"Processing group: {group_name}")

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(group_name + "-"):
            continue

        try:
            html_doc = tmp_dir / filename
            stdlog(f"Parsing: {html_doc}")
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as file:
                soup = BeautifulSoup(file, "html.parser")

            base_url = find_slug_by_md5(group_name, extract_md5_from_filename(str(html_doc))) or ""
            base_url = base_url.rstrip("/")

            for card in soup.select(".op-card"):
                victim_tag = card.select_one(".op-title")
                if not victim_tag:
                    continue

                victim = victim_tag.get_text(" ", strip=True)
                if not victim:
                    continue

                description_tag = card.select_one(".op-desc")
                description = description_tag.get_text(" ", strip=True) if description_tag else ""

                status_tag = card.select_one(".countdown")
                status = status_tag.get_text(" ", strip=True) if status_tag else ""
                if status:
                    description = " | ".join(part for part in [description, f"Status: {status}"] if part)

                link_tag = card.select_one("a[href]")
                post_url = ""
                if link_tag and base_url:
                    post_url = urljoin(base_url + "/", link_tag["href"])
                elif base_url:
                    post_url = base_url

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website="",
                    published="",
                    post_url=post_url,
                    country="",
                )
        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")


if __name__ == "__main__":
    main()
