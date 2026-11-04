#!/usr/bin/env python3
"""Summarize the latest scrape and parser run for the daily parser review."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp"
PARSERS = ROOT / "bin" / "_parsers"

# Add only verified group/parser aliases here. API parsers are handled by suffix.
ALIASES = {
    "apos security": ["apos"],
    "crazy hunter team": ["crazyhunter-api"],
    "hunters international": ["hunters-api"],
    "j group": ["J"],
    "kawa": ["kawa4096"],
    "mamona ransomware": ["mamona-api"],
}


def key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def coverage():
    result = {}
    for path in PARSERS.glob("*.py"):
        stem = path.stem
        group = stem[:-4] if stem.endswith("-api") else stem
        result.setdefault(key(group), []).append(stem)
    for group, parsers in ALIASES.items():
        result.setdefault(key(group), []).extend(parsers)
    return result


def report(manifest, parser_results):
    if (manifest.get("run_id") and parser_results.get("run_id")
            and manifest["run_id"] != parser_results["run_id"]):
        raise ValueError("Scrape and parser results belong to different runs")
    covered = coverage()
    candidates = []
    for location in manifest["locations"]:
        if location["status"] != "succeeded":
            continue
        group = location["group"]
        if key(group) not in covered:
            candidates.append({"group": group, "url": location["url"],
                               "html_path": location["html_path"]})
    return {"scrape_finished_at": manifest["finished_at"],
            "parser_finished_at": parser_results["finished_at"],
            "uncovered_candidates": candidates,
            "parser_issues": [item for item in parser_results["parsers"]
                              if item["status"] != "completed"]}


if __name__ == "__main__":
    state = json.loads((TMP / "maintenance-pipeline.json").read_text(encoding="utf-8"))
    if state.get("status") != "succeeded":
        raise SystemExit("Latest maintenance pipeline has not succeeded")
    manifest = json.loads((TMP / "scrape-manifest.json").read_text(encoding="utf-8"))
    results = json.loads((TMP / "parser-results.json").read_text(encoding="utf-8"))
    if not manifest.get("run_id") or manifest["run_id"] != state.get("started_at"):
        raise SystemExit("Scrape manifest does not belong to the latest pipeline")
    if results.get("run_id") != state.get("started_at"):
        raise SystemExit("Parser results do not belong to the latest pipeline")
    print(json.dumps(report(manifest, results), indent=2, ensure_ascii=False))
