#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal parser for Coinbasecartel (new layout)
- Parses company rows from the Companies list
- Extracts victim, detail URL, website, optional description
- Matches ransomware.live minimal ingestion style
"""

import os, datetime, sys, re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------
# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


BASE_URL = os.getenv(
    "BASE_URL",
    "http://fjg4zi4opkxkvdz7mvwp7h6goe4tcby3hhkrz43pht4j3vakhy75znyd.onion"
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _group_name_from_self() -> str:
    script_path = os.path.abspath(__file__)
    if os.path.islink(script_path):
        original_path = os.readlink(script_path)
        if not os.path.isabs(original_path):
            original_path = os.path.join(os.path.dirname(script_path), original_path)
        return os.path.basename(original_path).replace(".py", "")
    return os.path.basename(script_path).replace(".py", "")


def _normalize_post_url(href: str) -> str:
    if not href:
        return ""
    if href.startswith("/"):
        return BASE_URL.rstrip("/") + href
    return href


# ------------------------------------------------------------
# Main parser
# ------------------------------------------------------------
def main():
    group_name = _group_name_from_self()

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(group_name + "-"):
            continue

        try:
            html_doc = tmp_dir / filename
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, "html.parser")

            # Current layout: target rows in the dashboard table.
            rows = soup.select(".target-row")
            for row in rows:
                # Victim name
                name_tag = row.select_one(".target-name")
                victim = name_tag.get_text(" ", strip=True).replace("NEW", "").strip() if name_tag else ""
                victim = re.sub(r"^[\s\-–—]+", "", victim).strip()
                if not victim:
                    continue

                # Detail URL
                link_tag = row.select_one(".target-actions a[href]")
                post_url = _normalize_post_url(link_tag["href"]) if link_tag else ""

                website = ""

                industry = row.select_one(".target-industry")
                revenue = row.select_one(".target-rev")
                description_parts = []
                if industry:
                    description_parts.append(f"Industry: {industry.get_text(' ', strip=True)}")
                if revenue:
                    description_parts.append(f"Revenue: {revenue.get_text(' ', strip=True)}")
                description = " | ".join(description_parts)

                published = ""
                
                appender(
                    victim=victim,
                    group_name=group_name,
                    description=description,
                    website=website,
                    published=str(published),
                    post_url=post_url,
                    country=""
                )

                """
                print('victim:', victim)
                print('post_url:', post_url)
                print('website:', website)
                print('description:', description)
                print('-' * 40)
                """

        except Exception as e:
            errlog(
                f"{group_name} - parsing fail with error: {e} in file: {filename}"
            )


if __name__ == "__main__":
    main()
