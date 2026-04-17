import os
import re
from pathlib import Path

def list_scrape_results():
    tmp_dir = Path("tmp")
    if not tmp_dir.exists():
        print("Error: tmp directory not found.")
        return

    # Error indicators in Firefox/Playwright error pages
    ERROR_KEYWORDS = [
        "dnsNotFound", "connectionFailure", "netTimeout", "neterror",
        "Server Not Found", "Unable to connect", "Connection has timed out"
    ]

    print(f"{'Group':<20} | {'Status':<10} | {'Site Title / Info'}")
    print("-" * 120)

    success_count = 0
    failure_count = 0
    results = []

    for html_file in tmp_dir.glob("*.html"):
        try:
            with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000) # Read first 10KB
            
            is_error = False
            for kw in ERROR_KEYWORDS:
                if kw.lower() in content.lower():
                    is_error = True
                    break
            
            filename = html_file.name
            group = filename.split("-")[0]

            if not is_error:
                # Extract Title
                title = "No Title Found"
                title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title = re.sub(r"\s+", " ", title_match.group(1)).strip()
                
                # Check for empty or very small files that might be blank pages
                if len(content.strip()) < 500:
                    title = "[Warning: Very small/empty page]"

                results.append((group, "SUCCESS", title[:80]))
                success_count += 1
            else:
                failure_count += 1
                # results.append((group, "FAILURE", "Error Page")) # Optional: skip failures to keep list clean
        except Exception:
            continue

    # Sort and print only successes
    for group, status, info in sorted(results):
        print(f"{group:<20} | {status:<10} | {info}")

    print("-" * 120)
    print(f"Summary: {success_count} SUCCESSES, {failure_count} FAILURES identified in tmp/.")

if __name__ == "__main__":
    list_scrape_results()
