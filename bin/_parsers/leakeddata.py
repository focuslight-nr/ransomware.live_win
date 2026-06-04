#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from shared_utils import appender, errlog, extract_md5_from_filename, find_slug_by_md5, stdlog


script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", str(project_root))
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def _table_fields(table):
    fields = {}
    for row in table.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        key = cells[0].get_text(" ", strip=True).rstrip(":").lower()
        value = cells[1].get_text(" ", strip=True)
        fields[key] = value
    return fields


def _download_url(table, base_url):
    form = table.select_one("form[action]")
    if not form or not base_url:
        return base_url

    action = form.get("action", "")
    params = {}
    for input_tag in form.select("input[name]"):
        name = input_tag.get("name")
        if name == "csrfmiddlewaretoken":
            continue
        params[name] = input_tag.get("value", "")

    url = urljoin(base_url.rstrip("/") + "/", action)
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def main():
    group_name = "leakeddata"
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

            for block in soup.select(".block_1"):
                table = block.find("table")
                if not table:
                    continue

                fields = _table_fields(table)
                victim = fields.get("company", "").strip()
                if not victim:
                    continue

                details = []
                for label in ("revenue", "status", "total downloads", "company info"):
                    value = fields.get(label, "").strip()
                    if value:
                        details.append(f"{label.title()}: {value}")

                appender(
                    victim=victim,
                    group_name=group_name,
                    description=" | ".join(details),
                    website="",
                    published="",
                    post_url=_download_url(table, base_url),
                    country="",
                )
        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")


if __name__ == "__main__":
    main()
