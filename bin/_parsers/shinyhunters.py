
import string
import os
from bs4 import BeautifulSoup
from shared_utils import stdlog, errlog, appender

def main():
    '''
    Parser for shinyhunters
    '''
    for filename in filter(lambda f: f.startswith('shinyhunters-'), os.listdir('tmp')):
        stdlog(f"Processing {filename}")
        with open(f'tmp/{filename}', 'r', encoding='utf-8') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # All victim cards are in <article class="card ...">
        articles = soup.find_all('article', class_='card')
        
        for article in articles:
            h3 = article.find('h3')
            if not h3:
                continue
                
            victim_name = h3.get_text().strip()
            
            # Description is in <p> within <section class="front">
            description_p = article.find('p')
            description = description_p.get_text().strip() if description_p else ""
            
            # Date can be extracted from data-updated attribute or the meta span
            # data-updated="2026-03-10T16:20:00Z"
            published_date = article.get('data-updated', '')
            if published_date:
                # Convert 2026-03-10T16:20:00Z to 2026-03-10 16:20:00.000000
                published_date = published_date.replace('T', ' ').replace('Z', '.000000')
            else:
                # Fallback to text: Updated: 10 Mar 2026
                # Looking for meta info with clock icon
                meta_row = article.find('div', class_='meta')
                if meta_row:
                    meta_date = meta_row.find('span', string=lambda x: x and 'Updated:' in x)
                    if meta_date:
                        published_date = meta_date.get_text().replace('Updated:', '').strip()
            
            # Check for website in description or name (e.g., cfgi.com, Pathstone.com)
            website = ""
            if '(' in victim_name and ')' in victim_name:
                website = victim_name.split('(')[-1].split(')')[0].strip()
            elif '.' in victim_name and ' ' not in victim_name:
                website = victim_name

            # Add victim using the correct 'appender' function
            appender(victim_name, 'shinyhunters', description, website, published_date)

if __name__ == '__main__':
    # For standalone testing if needed
    main()
