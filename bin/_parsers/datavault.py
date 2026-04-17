import os
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv


# Load environment
# -------------------- CONFIG --------------------
from shared_utils import appender, stdlog, errlog
# Use robust path resolution for Windows/CLI consistency
script_dir = Path(__file__).resolve().parent
home = script_dir.parent.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

home_env = os.getenv("RANSOMWARELIVE_HOME", ".")
tmp_dir = Path(home_env) / os.getenv("TMP_DIR", "tmp").strip("/")


def extract_text_from_block(block, label):
    """Extracts the value corresponding to a label in the same block."""
    labels = block.find_all("div", class_="main_block_ul")
    for div in labels:
        items = div.find_all("div", class_="main_block_li")
        if len(items) == 2 and label.lower() in items[0].text.strip().lower():
            return items[1].text.strip()
    return ""

def main():
    script_path = os.path.abspath(__file__)
    group_name = os.path.basename(script_path).replace('.py','')

    for filename in os.listdir(tmp_dir):
        if not filename.startswith(group_name + '-'):
            continue

        html_path = tmp_dir / filename
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

                victims = soup.find_all("div", class_="main_block")

                for victim in victims:
                    try:
                        name = victim.find("div", class_="main_block_title").text.strip()
                        revenue = extract_text_from_block(victim, "Revenue")
                        employees = extract_text_from_block(victim, "Employees")
                        disclosures = extract_text_from_block(victim, "Disclosures")

                        notes_div = victim.find("div", class_="notes-content")
                        paragraphs = notes_div.find_all("p") if notes_div else []

                        description = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())

                    
                        """
                        appender(
                            victim=name,
                            group_name=group_name,
                            description=description,
                        )
                        """
                        print('name:',name)
                        print('description:',description)
                        print('*'*10)
                    except Exception as e:
                        errlog(f"Error parsing victim block in {filename}: {e}")
        except Exception as e:
            errlog(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    main()
