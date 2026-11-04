#!/usr/bin/env python3
"""Ransomware.live GUI — aiohttp web server"""
import asyncio
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web
from bin.review_acquisition import report as build_review_report

PORT = 8080
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"
GROUPS_FILE = DB_DIR / "groups.json"
VICTIMS_FILE = DB_DIR / "victims.json"
BIN_DIR = PROJECT_ROOT / "bin"
STATIC_DIR = Path(__file__).resolve().parent / "static"
TMP_DIR = PROJECT_ROOT / os.getenv("TMP_DIR", "tmp").strip("/")

_running_jobs: dict[str, dict] = {}


# ── helpers ────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = path.with_name(f"{path.stem}.bak_{ts}{path.suffix}")
    shutil.copy2(path, dst)
    return dst


def _job_id() -> str:
    return f"{int(time.time() * 1000)}"


# ── static ──────────────────────────────────────────────────────────────────

async def handle_index(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC_DIR / "index.html")


async def handle_theme_editor(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC_DIR / "theme-editor.html")


# ── groups API ──────────────────────────────────────────────────────────────

async def api_groups_list(request: web.Request) -> web.Response:
    groups = _load_json(GROUPS_FILE)
    q = request.rel_url.query.get("q", "").lower()
    if q:
        groups = [g for g in groups if q in g["name"].lower()]
    return web.json_response(groups)


async def api_group_get(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    groups = _load_json(GROUPS_FILE)
    for g in groups:
        if g["name"] == name:
            return web.json_response(g)
    raise web.HTTPNotFound(text=f"Group '{name}' not found")


async def api_group_update(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    body = await request.json()
    groups = _load_json(GROUPS_FILE)
    for i, g in enumerate(groups):
        if g["name"] == name:
            backup = _backup(GROUPS_FILE)
            # only allow safe field updates
            for field in ("date", "meta", "description", "contact", "locations", "profile"):
                if field in body:
                    groups[i][field] = body[field]
            _save_json(GROUPS_FILE, groups)
            return web.json_response({"ok": True, "backup": str(backup.name)})
    raise web.HTTPNotFound(text=f"Group '{name}' not found")


async def api_group_create(request: web.Request) -> web.Response:
    body = await request.json()
    name = body.get("name", "").strip().lower()
    slug = body.get("slug", "").strip()
    if not name:
        raise web.HTTPBadRequest(text="name required")
    if not slug:
        raise web.HTTPBadRequest(text="slug (initial URL) required")
    groups = _load_json(GROUPS_FILE)
    if any(g["name"] == name for g in groups):
        raise web.HTTPBadRequest(text=f"Group '{name}' already exists")
    import tldextract
    if not (slug.startswith("http://") or slug.startswith("https://")):
        slug = "http://" + slug
    ext = tldextract.extract(slug)
    fqdn = (ext.subdomain + "." if ext.subdomain else "") + ext.domain + "." + ext.suffix
    new_group = {
        "name": name,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "meta": None,
        "description": body.get("description") or None,
        "contact": None,
        "locations": [{
            "fqdn": fqdn,
            "title": None,
            "slug": slug,
            "available": False,
            "updated": None,
            "lastscrape": "2021-01-01 00:00:00.000000",
            "enabled": True,
            "type": "DLS",
        }],
        "profile": [],
    }
    backup = _backup(GROUPS_FILE)
    groups.append(new_group)
    _save_json(GROUPS_FILE, groups)
    return web.json_response({"ok": True, "group": new_group, "backup": str(backup.name)})


async def api_group_delete(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    groups = _load_json(GROUPS_FILE)
    new_groups = [g for g in groups if g["name"] != name]
    if len(new_groups) == len(groups):
        raise web.HTTPNotFound(text=f"Group '{name}' not found")
    backup = _backup(GROUPS_FILE)
    _save_json(GROUPS_FILE, new_groups)
    return web.json_response({"ok": True, "backup": str(backup.name)})


async def api_group_toggle_location(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    body = await request.json()
    slug = body.get("slug")
    groups = _load_json(GROUPS_FILE)
    for i, g in enumerate(groups):
        if g["name"] == name:
            for loc in g["locations"]:
                if loc.get("slug") == slug:
                    loc["enabled"] = not loc.get("enabled", True)
                    backup = _backup(GROUPS_FILE)
                    _save_json(GROUPS_FILE, groups)
                    return web.json_response({"ok": True, "enabled": loc["enabled"],
                                              "backup": str(backup.name)})
            raise web.HTTPBadRequest(text="Location not found")
    raise web.HTTPNotFound(text=f"Group '{name}' not found")


async def api_group_delete_location(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    body = await request.json()
    slug = body.get("slug")
    groups = _load_json(GROUPS_FILE)
    for i, g in enumerate(groups):
        if g["name"] == name:
            before = len(g["locations"])
            g["locations"] = [loc for loc in g["locations"] if loc.get("slug") != slug]
            if len(g["locations"]) == before:
                raise web.HTTPBadRequest(text="Location not found")
            backup = _backup(GROUPS_FILE)
            _save_json(GROUPS_FILE, groups)
            return web.json_response({"ok": True, "backup": str(backup.name)})
    raise web.HTTPNotFound(text=f"Group '{name}' not found")


async def api_group_add_location(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    body = await request.json()
    slug = body.get("slug", "").strip()
    if not slug:
        raise web.HTTPBadRequest(text="slug required")
    import tldextract
    import validators
    if not (slug.startswith("http://") or slug.startswith("https://")):
        slug = "http://" + slug
    ext = tldextract.extract(slug)
    fqdn = (ext.subdomain + "." if ext.subdomain else "") + ext.domain + "." + ext.suffix
    new_loc = {
        "fqdn": fqdn,
        "title": None,
        "slug": slug,
        "available": False,
        "updated": None,
        "lastscrape": "2021-01-01 00:00:00.000000",
        "enabled": True,
        "type": body.get("type", "DLS"),
    }
    groups = _load_json(GROUPS_FILE)
    for i, g in enumerate(groups):
        if g["name"] == name:
            if any(loc["slug"] == slug for loc in g["locations"]):
                raise web.HTTPBadRequest(text="Location already exists")
            backup = _backup(GROUPS_FILE)
            groups[i]["locations"].append(new_loc)
            _save_json(GROUPS_FILE, groups)
            return web.json_response({"ok": True, "location": new_loc, "backup": str(backup.name)})
    raise web.HTTPNotFound(text=f"Group '{name}' not found")


# ── victims API ──────────────────────────────────────────────────────────────

async def api_victims_list(request: web.Request) -> web.Response:
    victims = _load_json(VICTIMS_FILE)
    q = request.rel_url.query
    search = q.get("q", "").lower()
    group = q.get("group", "").lower()
    country = q.get("country", "").lower()
    activity = q.get("activity", "").lower()
    sort = q.get("sort", "discovered")
    order = q.get("order", "desc")
    limit = int(q.get("limit", 100))
    offset = int(q.get("offset", 0))

    if search:
        victims = [v for v in victims if search in v.get("post_title", "").lower()
                   or search in v.get("group_name", "").lower()
                   or search in v.get("website", "").lower()]
    if group:
        victims = [v for v in victims if v.get("group_name", "").lower() == group]
    if country:
        victims = [v for v in victims if v.get("country", "").lower() == country]
    if activity:
        victims = [v for v in victims if v.get("activity", "").lower() == activity]

    def sort_key(v):
        val = v.get(sort, "") or ""
        return val

    victims.sort(key=sort_key, reverse=(order == "desc"))
    total = len(victims)
    page = victims[offset: offset + limit]
    return web.json_response({"total": total, "victims": page})


async def api_victims_facets(request: web.Request) -> web.Response:
    victims = _load_json(VICTIMS_FILE)
    countries   = sorted({v.get("country")    or "" for v in victims if v.get("country")})
    activities  = sorted({v.get("activity")   or "" for v in victims if v.get("activity")})
    group_names = sorted({v.get("group_name") or "" for v in victims if v.get("group_name")})
    return web.json_response({"countries": countries, "activities": activities,
                              "group_names": group_names})


async def api_victim_update(request: web.Request) -> web.Response:
    idx_str = request.match_info["idx"]
    body = await request.json()
    victims = _load_json(VICTIMS_FILE)
    # find by post_title + group_name as composite key
    title = body.get("post_title")
    group = body.get("group_name")
    target = None
    for v in victims:
        if v.get("post_title") == title and v.get("group_name") == group:
            target = v
            break
    if target is None:
        raise web.HTTPNotFound(text="Victim not found")
    backup = _backup(VICTIMS_FILE)
    for field in ("country", "activity", "website", "description"):
        if field in body:
            target[field] = body[field]
    _save_json(VICTIMS_FILE, victims)
    return web.json_response({"ok": True, "backup": str(backup.name)})


# ── stats API ────────────────────────────────────────────────────────────────

async def api_stats(request: web.Request) -> web.Response:
    groups = _load_json(GROUPS_FILE)
    victims = _load_json(VICTIMS_FILE)

    victims_by_group: dict[str, int] = {}
    for v in victims:
        gn = v.get("group_name", "unknown")
        victims_by_group[gn] = victims_by_group.get(gn, 0) + 1

    top_groups = sorted(victims_by_group.items(), key=lambda x: x[1], reverse=True)[:15]

    activity_dist: dict[str, int] = {}
    for v in victims:
        a = v.get("activity") or "Not Found"
        activity_dist[a] = activity_dist.get(a, 0) + 1

    country_dist: dict[str, int] = {}
    for v in victims:
        c = v.get("country") or "Unknown"
        country_dist[c] = country_dist.get(c, 0) + 1
    top_countries = sorted(country_dist.items(), key=lambda x: x[1], reverse=True)[:15]

    # recent 20 victims sorted by discovered
    recent = sorted(
        [v for v in victims if v.get("discovered")],
        key=lambda v: v["discovered"],
        reverse=True,
    )[:20]

    active_groups = sum(
        1 for g in groups
        if any(loc.get("available") for loc in g.get("locations", []))
    )

    return web.json_response({
        "total_groups": len(groups),
        "total_victims": len(victims),
        "active_groups": active_groups,
        "top_groups": [{"name": k, "count": v} for k, v in top_groups],
        "activity_dist": [{"activity": k, "count": v} for k, v in
                          sorted(activity_dist.items(), key=lambda x: x[1], reverse=True)[:15]],
        "top_countries": [{"country": k, "count": v} for k, v in top_countries],
        "recent_victims": recent,
    })


async def api_victims_export_csv(request: web.Request) -> web.Response:
    import csv, io
    victims = _load_json(VICTIMS_FILE)
    q = request.rel_url.query
    search = q.get("q", "").lower()
    group = q.get("group", "").lower()
    country = q.get("country", "").lower()
    activity = q.get("activity", "").lower()
    if search:
        victims = [v for v in victims if search in v.get("post_title", "").lower()
                   or search in v.get("group_name", "").lower()
                   or search in v.get("website", "").lower()]
    if group:
        victims = [v for v in victims if v.get("group_name", "").lower() == group]
    if country:
        victims = [v for v in victims if v.get("country", "").lower() == country]
    if activity:
        victims = [v for v in victims if v.get("activity", "").lower() == activity]

    cols = ["group_name", "post_title", "website", "country", "activity",
            "discovered", "published", "description", "post_url"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(victims)
    return web.Response(
        text=buf.getvalue(),
        content_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=victims_export.csv"},
    )


async def api_parsers_list(request: web.Request) -> web.Response:
    parsers_dir = BIN_DIR / "_parsers"
    if not parsers_dir.exists():
        return web.json_response([])
    names = sorted(
        p.stem for p in parsers_dir.glob("*.py")
    )
    return web.json_response(names)


async def api_maintenance_review(request: web.Request) -> web.Response:
    """Return only artifacts belonging to the latest completed pipeline."""
    state_path = TMP_DIR / "maintenance-pipeline.json"
    if not state_path.exists():
        return web.json_response({"available": False, "reason": "No maintenance run recorded"})
    try:
        state = _load_json(state_path)
        if state.get("status") != "succeeded":
            return web.json_response({"available": False,
                                      "reason": "Latest maintenance run is not complete",
                                      "pipeline": state})
        manifest = _load_json(TMP_DIR / "scrape-manifest.json")
        parsers = _load_json(TMP_DIR / "parser-results.json")
        run_id = state.get("started_at")
        if not run_id or manifest.get("run_id") != run_id or parsers.get("run_id") != run_id:
            return web.json_response({"available": False,
                                      "reason": "Review artifacts are not from the latest run",
                                      "pipeline": state})
        review = build_review_report(manifest, parsers)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return web.json_response({"available": False,
                                  "reason": f"Review artifacts unavailable: {exc}",
                                  "pipeline": state})
    return web.json_response({"available": True, "pipeline": state,
                              "manifest": manifest, "parser_results": parsers,
                              "review": review})


async def api_review_html(request: web.Request) -> web.Response:
    """Show a saved page as inert text, restricted to the latest run's manifest."""
    try:
        state = _load_json(TMP_DIR / "maintenance-pipeline.json")
        manifest = _load_json(TMP_DIR / "scrape-manifest.json")
    except (OSError, ValueError):
        raise web.HTTPNotFound(text="Review artifacts unavailable")
    if state.get("status") != "succeeded" or manifest.get("run_id") != state.get("started_at"):
        raise web.HTTPNotFound(text="No completed matching run")
    group = request.rel_url.query.get("group")
    url = request.rel_url.query.get("url")
    location = next((item for item in manifest.get("locations", [])
                     if item.get("group") == group and item.get("url") == url
                     and item.get("status") == "succeeded"), None)
    if not location or not location.get("html_path"):
        raise web.HTTPNotFound(text="Saved HTML not found")
    path = Path(location["html_path"]).resolve()
    if not path.is_relative_to(TMP_DIR.resolve()):
        raise web.HTTPForbidden(text="HTML path outside tmp")
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        raise web.HTTPNotFound(text="Saved HTML unavailable")
    return web.Response(text=content, content_type="text/plain", charset="utf-8",
                        headers={"X-Content-Type-Options": "nosniff"})


# ── runner API ───────────────────────────────────────────────────────────────

async def api_run(request: web.Request) -> web.Response:
    body = await request.json()
    action = body.get("action")  # "scrape" or "parse"
    group = body.get("group", "").strip()
    force = bool(body.get("force", False))

    if action not in ("scrape", "parse"):
        raise web.HTTPBadRequest(text="action must be scrape or parse")
    if not group:
        raise web.HTTPBadRequest(text="group required")

    job_id = _job_id()
    _running_jobs[job_id] = {"status": "running", "lines": [], "returncode": None}

    asyncio.create_task(_run_subprocess(job_id, action, group, force))
    return web.json_response({"job_id": job_id})


async def _run_subprocess(job_id: str, action: str, group: str, force: bool) -> None:
    script = BIN_DIR / f"{action}.py"
    cmd = [sys.executable, str(script), "-G", group]
    if force:
        cmd.append("-F")

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = 0x08000000  # CREATE_NO_WINDOW

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BIN_DIR)
    env.setdefault("RANSOMWARELIVE_HOME", str(PROJECT_ROOT))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJECT_ROOT),
            env=env,
            **({} if sys.platform != "win32" else {"creationflags": creation_flags}),
        )
        _running_jobs[job_id]["pid"] = proc.pid

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            _running_jobs[job_id]["lines"].append(line.decode("utf-8", errors="replace").rstrip())

        await proc.wait()
        _running_jobs[job_id]["returncode"] = proc.returncode
        _running_jobs[job_id]["status"] = "done"
    except Exception as exc:
        _running_jobs[job_id]["lines"].append(f"[ERROR] {exc}")
        _running_jobs[job_id]["status"] = "error"
        _running_jobs[job_id]["returncode"] = -1


async def api_job_status(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    job = _running_jobs.get(job_id)
    if job is None:
        raise web.HTTPNotFound(text="Job not found")
    offset = int(request.rel_url.query.get("offset", 0))
    return web.json_response({
        "status": job["status"],
        "returncode": job["returncode"],
        "lines": job["lines"][offset:],
        "total_lines": len(job["lines"]),
    })


async def api_jobs_list(request: web.Request) -> web.Response:
    return web.json_response([
        {"job_id": jid, "status": j["status"], "returncode": j["returncode"]}
        for jid, j in _running_jobs.items()
    ])


# ── app factory ──────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/theme-editor.html", handle_theme_editor)
    app.router.add_static("/static", STATIC_DIR)

    # groups
    app.router.add_get("/api/groups", api_groups_list)
    app.router.add_post("/api/groups", api_group_create)
    app.router.add_get("/api/groups/{name}", api_group_get)
    app.router.add_put("/api/groups/{name}", api_group_update)
    app.router.add_delete("/api/groups/{name}", api_group_delete)
    app.router.add_post("/api/groups/{name}/locations", api_group_add_location)
    app.router.add_delete("/api/groups/{name}/locations", api_group_delete_location)
    app.router.add_patch("/api/groups/{name}/locations", api_group_toggle_location)

    # victims
    app.router.add_get("/api/victims", api_victims_list)
    app.router.add_get("/api/victims/facets", api_victims_facets)
    app.router.add_get("/api/victims/export.csv", api_victims_export_csv)
    app.router.add_put("/api/victims/{idx}", api_victim_update)

    # stats
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/parsers", api_parsers_list)
    app.router.add_get("/api/maintenance-review", api_maintenance_review)
    app.router.add_get("/api/maintenance-review/html", api_review_html)

    # runner
    app.router.add_post("/api/run", api_run)
    app.router.add_get("/api/jobs", api_jobs_list)
    app.router.add_get("/api/jobs/{job_id}", api_job_status)

    return app
