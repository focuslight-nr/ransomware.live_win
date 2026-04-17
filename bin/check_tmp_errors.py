import os
import re
from pathlib import Path

def identify_connection_failures():
    tmp_dir = Path("tmp")
    if not tmp_dir.exists():
        print("Error: tmp directory not found.")
        return

    # Error indicators in Firefox/Playwright error pages
    ERROR_KEYWORDS = {
        "dnsNotFound": "Server Not Found",
        "connectionFailure": "Unable to connect",
        "netTimeout": "Connection has timed out",
        "neterror": "Generic Network Error"
    }

    print(f"{'Group':<20} | {'Error Type':<20} | {'Onion URL (Extracted)'}")
    print("-" * 120)

    failure_map = {}

    for html_file in tmp_dir.glob("*.html"):
        try:
            # Read first part of the file
            with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(5000) # Read first 5KB to find URL in longer error pages
            
            found_error = None
            for key, label in ERROR_KEYWORDS.items():
                if key.lower() in content.lower() or label.lower() in content.lower():
                    found_error = label
                    break
            
            if found_error:
                # Extract URL from standard Firefox error page structure
                # <p id="errorShortDesc">We can't connect to the server at [URL].</p>
                # or <p id="errorShortDesc">Nightly can遯ｶ蜀ｲ find the server at [URL].</p>
                url = "N/A"
                match = re.search(r'connect to the server at ([^.<>"\s]+\.onion)', content)
                if not match:
                    match = re.search(r'find the server at ([^.<>"\s]+\.onion)', content)
                if not match:
                    # Generic fallback for any .onion string found near the error
                    match = re.search(r'([a-z2-7]{16,}\.onion)', content, re.IGNORECASE)
                
                if match:
                    url = match.group(1)

                filename = html_file.name
                group = filename.split("-")[0]
                failure_map[group] = (found_error, url)
        except Exception:
            continue

    for group, (error, url) in sorted(failure_map.items()):
        print(f"{group:<20} | {error:<20} | {url}")

    print("-" * 120)
    print(f"Total groups with connection failure pages: {len(failure_map)}")

if __name__ == "__main__":
    identify_connection_failures()
