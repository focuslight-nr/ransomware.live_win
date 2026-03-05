"""
    Parser for XP95
    Extracts victims from the 'directories' JavaScript object in the mock Windows 95 desktop.
"""

import os
import re
import json
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, stdlog, errlog
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
home = Path(__file__).resolve().parent.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

tmp_dir = home / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    for filename in os.listdir(tmp_dir):
        if filename.startswith('xp95-') and filename.endswith('.html'):
            file_path = tmp_dir / filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract the 'directories' object using regex
                # We look for 'const directories = { ... };'
                match = re.search(r'const\s+directories\s*=\s*(\{.*?\});', content, re.DOTALL)
                if match:
                    directories_str = match.group(1)
                    
                    # The extracted string might not be valid JSON (e.g., trailing commas, unquoted keys)
                    # For XP95, it looks like:
                    # {
                    #   "For sale !!":[
                    #   ],
                    #   "Ransom !!":[
                    #     {name:"eholo health",path:"./files/eholo.txt"},
                    #   ],
                    #   "News & Update":[
                    #   ]
                    # }
                    
                    # Convert JS-like object to JSON
                    # 1. Quote unquoted keys (e.g., name: -> "name":)
                    directories_str = re.sub(r'(\w+):', r'"\1":', directories_str)
                    # 2. Remove trailing commas before closing braces/brackets
                    directories_str = re.sub(r',\s*([\}\]])', r'\1', directories_str)
                    
                    try:
                        directories = json.loads(directories_str)
                        
                        # Extract victims from "For sale !!" and "Ransom !!"
                        categories = ["For sale !!", "Ransom !!"]
                        md5_hash = extract_md5_from_filename(filename)
                        base_url = find_slug_by_md5('xp95', md5_hash) or ""
                        
                        for category in categories:
                            if category in directories:
                                for item in directories[category]:
                                    victim_name = item.get("name", "").strip()
                                    if victim_name:
                                        # For XP95, we don't have a specific pubdate or description in the list
                                        # The path might lead to more info, but for now we take the name.
                                        post_url = ""
                                        if item.get("path"):
                                            path = item["path"]
                                            if path.startswith("./"):
                                                path = path[2:]
                                            post_url = f"{base_url.rstrip('/')}/{path}"
                                        
                                        appender(victim_name, 'xp95', "", "", "", post_url)
                                        
                    except json.JSONDecodeError as je:
                        errlog(f"XP95 - JSON decode error in {filename}: {je}")
                else:
                    errlog(f"XP95 - 'directories' object not found in {filename}")
                    
            except Exception as e:
                errlog(f"XP95 - Parsing failed for {filename}: {e}")

if __name__ == "__main__":
    main()
