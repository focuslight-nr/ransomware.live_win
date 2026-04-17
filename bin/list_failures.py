import json
from pathlib import Path
import os

def list_failures():
    groups_path = Path("db/groups.json")
    if not groups_path.exists():
        print("Error: db/groups.json not found.")
        return

    with open(groups_path, "r", encoding="utf-8") as f:
        groups = json.load(f)

    print(f"{'Group':<20} | {'Status':<10} | {'Last Updated':<20} | {'Location'}")
    print("-" * 100)

    failure_count = 0
    total_count = 0

    for group in groups:
        for loc in group.get("locations", []):
            total_count += 1
            available = loc.get("available", True)
            if not available:
                failure_count += 1
                name = str(group.get("name", "N/A"))
                last_updated = str(loc.get("updated", "Never"))
                slug = str(loc.get("slug", "N/A"))
                print(f"{name:<20} | {'OFFLINE':<10} | {last_updated:<20} | {slug}")

    print("-" * 100)
    print(f"Summary: {failure_count} failures out of {total_count} total locations.")

if __name__ == "__main__":
    list_failures()
