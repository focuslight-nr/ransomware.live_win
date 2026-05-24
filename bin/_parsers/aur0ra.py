#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils import appender, errlog, stdlog


GROUP_NAME = "aur0ra"
FALLBACK_URL = "http://u6lieui2dakbctcjea2bz4r4q32r7t36nwljovqbv7mxs6o2smgxixid.onion"

script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
load_dotenv(dotenv_path=home / ".env")


def _tor_proxy():
    proxy = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")
    if proxy.startswith("socks5://"):
        proxy = "socks5h://" + proxy[len("socks5://") :]
    return {"http": proxy, "https": proxy}


def _base_url():
    groups_path = home / os.getenv("DB_DIR", "db").strip("/") / "groups.json"
    try:
        with open(groups_path, encoding="utf-8") as file:
            groups = json.load(file)
        group = next((item for item in groups if item.get("name") == GROUP_NAME), None)
        if group:
            for location in group.get("locations", []):
                slug = location.get("slug")
                if slug:
                    return slug.rstrip("/")
    except Exception as exc:
        errlog(f"[{GROUP_NAME}] Failed to read groups.json: {exc}")
    return FALLBACK_URL


def _published_date(blog):
    value = blog.get("dataPublishingDate") or blog.get("createdAt") or ""
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return ""


def _extra_infos(blog):
    extra = []
    for key, label in (
        ("tags", "tags"),
        ("folderName", "folder"),
        ("ftpLink1", "ftpLink1"),
        ("ftpLink2", "ftpLink2"),
        ("viewCount", "viewCount"),
    ):
        value = blog.get(key)
        if value in (None, "", []):
            continue
        extra.append({"key": label, "value": value})
    return extra


def _fetch_blogs(session, base_url, page=1, limit=20):
    url = urljoin(base_url + "/", f"api/blogs?page={page}&limit={limit}")
    response = session.get(url, timeout=90)
    response.raise_for_status()
    return response.json()


def main():
    base_url = _base_url()
    stdlog(f"[{GROUP_NAME}] Starting parser")

    session = requests.Session()
    session.proxies.update(_tor_proxy())

    try:
        first_page = _fetch_blogs(session, base_url)
    except Exception as exc:
        errlog(f"[{GROUP_NAME}] Error fetching API: {exc}")
        return

    blogs = list(first_page.get("blogs", []))
    pagination = first_page.get("pagination") or {}
    total_pages = int(pagination.get("totalPages") or 1)

    for page in range(2, total_pages + 1):
        try:
            page_data = _fetch_blogs(session, base_url, page=page)
            blogs.extend(page_data.get("blogs", []))
        except Exception as exc:
            errlog(f"[{GROUP_NAME}] Error fetching API page {page}: {exc}")

    if not blogs:
        errlog(f"[{GROUP_NAME}] No blogs found.")
        return

    for blog in blogs:
        victim = (blog.get("companyName") or "").strip()
        if not victim:
            continue

        public_url = blog.get("publicUrl") or f"/blog/{blog.get('slug', '')}"
        post_url = urljoin(base_url + "/", public_url.lstrip("/"))

        appender(
            victim=victim,
            group_name=GROUP_NAME,
            description=blog.get("description") or "",
            website="",
            published=_published_date(blog),
            post_url=post_url,
            country="",
            extra_infos=_extra_infos(blog),
        )

    stdlog(f"[{GROUP_NAME}] Parser finished. Parsed {len(blogs)} blogs.")


if __name__ == "__main__":
    main()
