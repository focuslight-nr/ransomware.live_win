import re
import os
import requests
import json
import sys

# URL for the markdown file
markdown_url = "https://raw.githubusercontent.com/fastfire/deepdarkCTI/main/ransomware_gang.md"

# Fetch the content from the URL
try:
    response = requests.get(markdown_url)
    response.raise_for_status()  # Raise an exception for bad status codes
    markdown_content = response.text
except requests.exceptions.RequestException as e:
    print(f"Error fetching markdown file: {e}")
    exit()

lines = markdown_content.splitlines()
commands = []
offline_urls = set()

for line in lines:
    if not line.startswith('|'):
        continue

    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 3:
        continue
    
    status = parts[2].strip().upper()
    
    # Support both .onion and clear web URLs - require a dot before the TLD/onion suffix
    url_match = re.search(r'(https?://[a-zA-Z0-9.-]+\.(?:onion|[a-zA-Z]{2,}))', line)
    if not url_match:
        continue
    
    url = url_match.group(1)

    if status == 'OFFLINE':
        offline_urls.add(url)
        continue

    if status != 'ONLINE':
        continue

    name_part = parts[1]
    name = re.sub(r'\[([^\]]+)\].*', r'\1', name_part)
    name = name.split('(')[0].strip()

    if not name or 'RANSOMWARE GROUP' in name or 'Name' in name:
        continue

    # Sanitize name for command line
    commands.append((name, url))

# Remove duplicates for commands
unique_commands = sorted(set(commands))

print(f"Found {len(unique_commands)} unique groups with ONLINE status to add.")
print(f"Found {len(offline_urls)} URLs with OFFLINE status to potentially remove.")

# --- Process OFFLINE URLs ---
if offline_urls:
    groups_file = "db/groups.json"
    if os.path.exists(groups_file):
        try:
            with open(groups_file, 'r', encoding='utf-8') as f:
                groups_data = json.load(f)
            
            modified = False
            for group in groups_data:
                original_locations = group.get('locations', [])
                # Filter out locations that are in the offline_urls list
                new_locations = [loc for loc in original_locations if loc.get('slug') not in offline_urls]
                
                if len(new_locations) != len(original_locations):
                    removed_count = len(original_locations) - len(new_locations)
                    print(f"[-] Group '{group['name']}': Removing {removed_count} OFFLINE location(s).")
                    group['locations'] = new_locations
                    modified = True
            
            if modified:
                with open(groups_file, 'w', encoding='utf-8') as f:
                    json.dump(groups_data, f, ensure_ascii=False, indent=4)
                print("[✓] Updated groups.json with OFFLINE URLs removed.")
        except Exception as e:
            print(f"Error processing OFFLINE URLs: {e}")

# --- Add ONLINE groups in-process (single read + single write) ---
# Reuse manage.py's helpers but bypass the per-call subprocess launch and the
# full read/write of groups.json that happened once per group. We load
# groups.json once, mutate it in memory, and write it back a single time.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manage

print("Adding ONLINE groups in-process...")

# Honor the scrape lock exactly like manage.py does before touching groups.json
lock_file_path = manage.home / 'tmp' / 'scrape.lock'
manage.wait_for_lock(lock_file_path)

groups = manage.openjson(manage.GROUPS_FILE)

# Index existing groups by name so lookups are O(1) instead of a linear scan
groups_by_name = {group['name']: group for group in groups}

added_groups = 0
added_locations = 0
skipped_duplicates = 0

for name, url in unique_commands:
    # Match manage.py's normalization (lowercase name, strip surrounding quotes)
    name = name.strip('"').lower()
    url = url.strip('"')

    group = groups_by_name.get(name)
    if group is None:
        new_group = manage.creategroup(name, url)
        groups.append(new_group)
        groups_by_name[name] = new_group
        added_groups += 1
        # Bluesky notification intentionally skipped for batch runs.
    else:
        existing_slugs = {loc['slug'] for loc in group['locations']}
        if url not in existing_slugs:
            group['locations'].append(manage.siteschema(url))
            added_locations += 1
        else:
            skipped_duplicates += 1

# Single write for the whole batch
manage.write_to_file(groups, manage.GROUPS_FILE)
print(
    f"[✓] Added {added_groups} new group(s), "
    f"{added_locations} new location(s), "
    f"skipped {skipped_duplicates} duplicate(s)."
)

print("Batch add process complete.")
