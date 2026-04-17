import os
import re
from pathlib import Path

# Paths
ORIGIN_PARSERS = Path("origin/ransomware.live/bin/_parsers")
DEST_PARSERS = Path("bin/_parsers")

# Mapping for files with different names
FILE_MAPPING = {
    "BrainCipher.py": "brain_cipher.py",
    "lockbit5.py": "lockbit5.0.py",
    "lapsus$.py": "lapsus$ group.py",
    "blackwater.py": "black water.py",
    "AuditTeam.py": "audit.py",
    "AiLock.py": "ailock.py",
    "ALP-001.py": "alp-001.py",
}

# The replacement block for path and import logic
PATH_REPLACEMENT = """# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")
"""

def sync_parsers():
    if not ORIGIN_PARSERS.exists():
        print(f"Error: {ORIGIN_PARSERS} not found.")
        return

    for src_file in ORIGIN_PARSERS.glob("*.py"):
        filename = src_file.name
        dest_filename = FILE_MAPPING.get(filename, filename.lower())
        dest_file = DEST_PARSERS / dest_filename

        with open(src_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # 1. Update imports
        # Remove old imports that we will replace or that are redundant
        content = content.replace("from shared_utils import appender, errlog", "")
        content = content.replace("from shared_utils import appender, stdlog, errlog", "")
        
        # 2. Replace path logic block
        # Look for the pattern used in origin parsers
        pattern = r"env_path = Path\(\"\.\./\.env\"\).*?tmp_dir = Path\(home \+ os\.getenv\(\"TMP_DIR\"\)\)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, PATH_REPLACEMENT, content, flags=re.DOTALL)
        else:
            # Fallback for slightly different patterns
            new_content = content.replace('tmp_dir = Path(home + os.getenv("TMP_DIR"))', PATH_REPLACEMENT)

        # 3. Fix potential undefined variables
        new_content = new_content.replace('Path(home + os.getenv("TMP_DIR"))', 'tmp_dir')

        # 4. Force UTF-8 encoding for opening HTML files (fixes cp932 error on Windows)
        # Handles both 'with open(...)' and 'file = open(...)'
        # Target: open(some_var, 'r') or open(some_var, "r")
        new_content = re.sub(r'open\(([^,)]+),\s*["\']r["\']\s*\)', 
                             r'open(\1, "r", encoding="utf-8", errors="ignore")', 
                             new_content)

        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    
    print("Sync completed successfully.")

if __name__ == "__main__":
    sync_parsers()
