import re
import subprocess
import os
import requests
import json

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
    
    # Support both .onion and clear web URLs
    url_match = re.search(r'(https?://[a-zA-Z0-9.-]+(?:\.onion|[a-zA-Z]{2,}))', line)
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
    sanitized_name = name.replace('"', '\"')
    commands.append(f'python bin/manage.py --force --add "{sanitized_name}" "{url}"')

# Remove duplicates for commands
unique_commands = sorted(list(set(commands)))

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

# --- Execute ONLINE commands ---
print("Executing add commands...")
for cmd in unique_commands:
    print(f"Executing: {cmd}")
    try:
        # Using os.system as it's simpler for this case
        os.system(cmd)
    except Exception as e:
        print(f"Error executing command: {e}")

print("Batch add process complete.")