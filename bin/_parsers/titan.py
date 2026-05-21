"""
    Parser for Titan group
    +----------------------------------------------+
    | Description | Website | published | post URL |
    +-----------------------+-----------+----------+
    |       X     |    X    |     X     |     X    |
    +-----------------------+-----------+----------+
"""

import os
import re
import json
import html
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import find_slug_by_md5, appender, extract_md5_from_filename, errlog, stdlog

# -------------------- CONFIG --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")

def main():
    group_name = 'titan'
    
    # Exclude list for names
    exclude_labels = {
        "Website", "Date of publication", "UTC", "Classic", "Compact", "Grid", "Tiles",
        "Leaked Data", "Awaiting Publication", "TERMS & CONDITIONS", "·", "Gallery",
        "Leak links", "Items whose publication date has already passed.",
        "Search posts in this section", "Search", "TITAN", " | ", "Terms and conditions",
        "404: This page could not be found.", "This page could not be found.", "AM", "PM", "at"
    }

    for filename in os.listdir(tmp_dir):
        if not filename.startswith('titan-') or not filename.endswith('.html'):
            continue
            
        html_doc = tmp_dir / filename
        try:
            with open(html_doc, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")
            next_f_data = []
            for s in soup.find_all("script"):
                s_content = s.text or ""
                if "self.__next_f.push" in s_content:
                    m = re.search(r'self\.__next_f\.push\((.*)\)', s_content, re.DOTALL)
                    if m:
                        arg = m.group(1).strip()
                        if arg.startswith('[') and arg.endswith(']'):
                            arg = arg[1:-1]
                        next_f_data.append(arg)

            scripts_text = "\n".join(next_f_data)
            # Replace escaped newlines and unescape quotes
            scripts_text = scripts_text.replace('\\n', '\n').replace('\\r', '\r')
            scripts_text = scripts_text.replace('\\"', '"').replace('\\\\', '\\')

            chunks = {}
            for line in scripts_text.splitlines():
                m = re.match(r'^\d+,"([0-9a-fA-F]+):(.*)$', line.strip())
                if m:
                    cid = m.group(1)
                    val = m.group(2)
                    if val.endswith('"'):
                        val = val[:-1]
                    chunks[cid] = val
                else:
                    m2 = re.match(r'^([0-9a-fA-F]+):(.*)$', line.strip())
                    if m2:
                        cid = m2.group(1)
                        val = m2.group(2)
                        if val.endswith('"'):
                            val = val[:-1]
                        chunks[cid] = val

            companies = []
            for cid, chunk_val in chunks.items():
                children = re.findall(r'"children":"([^"]+)"', chunk_val)
                names = [c for c in children if c not in exclude_labels and not c.startswith("www.") and not c.startswith("http")]
                
                if names:
                    company_name = names[0]
                    # Filter out names starting with $ or consist of special chars/digits
                    if company_name.startswith('$') or re.match(r'^[^a-zA-Z0-9]+$', company_name):
                        continue
                    
                    # Unescape unicode characters (e.g. \u0026)
                    try:
                        company_name = json.loads(f'"{company_name}"')
                    except Exception:
                        pass
                    
                    refs = re.findall(r'\$L([0-9a-fA-F]+)', chunk_val)
                    companies.append({
                        "name": company_name,
                        "refs": refs,
                        "website": "",
                        "date": "",
                        "leak_link": ""
                    })

            # Resolve references
            for c in companies:
                for ref in c["refs"]:
                    if ref in chunks:
                        ref_content = chunks[ref]
                        
                        href_match = re.search(r'"href":"https://([^"]+)/"', ref_content)
                        if href_match:
                            c["website"] = href_match.group(1)
                        
                        date_match = re.search(r'"dateTime":"([^"]+)"', ref_content)
                        if date_match:
                            c["date"] = date_match.group(1)
                        
                        leak_match = re.search(r'"leakLinks":\["([^"]+)"\]', ref_content)
                        if leak_match:
                            c["leak_link"] = leak_match.group(1)

                # Format published date
                pubdate = ""
                if c["date"]:
                    try:
                        dt = datetime.fromisoformat(c["date"].replace('Z', '+00:00'))
                        pubdate = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
                    except Exception:
                        pubdate = ""

                # Fallback website if empty and name is domain
                website = c["website"]
                if not website and re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', c["name"]):
                    website = c["name"]

                appender(
                    victim=c["name"],
                    group_name=group_name,
                    description="",
                    website=website,
                    published=pubdate,
                    post_url=c["leak_link"]
                )

        except Exception as e:
            errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
