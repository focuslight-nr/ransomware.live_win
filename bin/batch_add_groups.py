import re
import subprocess
import os
import requests

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

for line in lines:
    if not line.startswith('|') or '.onion' not in line:
        continue

    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 3:
        continue
    
    # Check if status is ONLINE
    if parts[2].strip().upper() != 'ONLINE':
        continue

    name_part = parts[1]
    
    name = re.sub(r'\[([^\]]+)\].*', r'\1', name_part)
    name = name.split('(')[0].strip()

    if not name or 'RANSOMWARE GROUP' in name or 'Name' in name:
        continue

    # Corrected regex for URL: do not include trailing ')'
    url_match = re.search(r'(https?://[a-z0-9.-]+\.onion)', line)
    if url_match:
        url = url_match.group(1)
        # Sanitize name for command line
        sanitized_name = name.replace('"', '\"')
        commands.append(f'python bin/manage.py --force --add "{sanitized_name}" "{url}"')

# Remove duplicates
unique_commands = sorted(list(set(commands)))

print(f"Found {len(unique_commands)} unique groups with .onion URLs to add.")
print("Executing commands...")

for cmd in unique_commands:
    print(f"Executing: {cmd}")
    try:
        # Using os.system as it's simpler for this case
        os.system(cmd)
    except Exception as e:
        print(f"Error executing command: {e}")

print("Batch add process complete.")