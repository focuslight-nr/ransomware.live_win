"""
    AiLock Parser
"""

import os
from bs4 import BeautifulSoup
from shared_utils import appender, errlog, stdlog, tmp_dir

def main():
    group_name = "ailock"
    
    for filename in os.listdir(tmp_dir):
        if filename.startswith(group_name + '-'):
            html_doc = tmp_dir / filename
            stdlog(f"Parsing {group_name} file: {filename}")
            
            try:
                with open(html_doc, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                
                # Victims are in div with class "news-card"
                news_cards = soup.find_all('div', class_='news-card')
                
                for card in news_cards:
                    # Title (Victim Name)
                    title_tag = card.find('h3')
                    if not title_tag:
                        continue
                    victim = title_tag.get_text(strip=True)
                    
                    # Date
                    date = ""
                    date_tag = card.find('span', class_='nes-text')
                    if date_tag:
                        date_text = date_tag.get_text(strip=True)
                        if "Coming soon" not in date_text:
                            date = date_text
                    
                    # Description and Website
                    # Structure: <h3>...</h3> <p><b>Date:</b><span>...</span></p> <p>website and more</p>
                    p_tags = card.find_all('p')
                    description = ""
                    website = ""
                    
                    if len(p_tags) >= 2:
                        desc_p = p_tags[1].get_text(strip=True)
                        # Often starts with domain
                        parts = desc_p.split(' ', 1)
                        if '.' in parts[0]:
                            website = parts[0]
                            if len(parts) > 1:
                                description = parts[1]
                        else:
                            description = desc_p
                    
                    appender(victim, group_name, description, website, date)
                    
            except Exception as e:
                errlog(f"{group_name} - parsing fail with error: {e} in file: {filename}")

if __name__ == "__main__":
    main()
