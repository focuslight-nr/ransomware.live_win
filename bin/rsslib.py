import json
from datetime import datetime
import hashlib, os
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
# import xml.etree.ElementTree as ET
import html
import xml.sax.saxutils as saxutils
from dotenv import load_dotenv
import requests
import pytz
from shared_utils import  stdlog, errlog 
from pathlib import Path
import base64
import argparse

# Load environment variables from ../.env
script_dir = Path(__file__).resolve().parent
home = script_dir.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

# Paths from environment variables
db_dir = home / os.getenv("DB_DIR", "db").strip("/")
data_dir = home / os.getenv("DATA_DIR", "data").strip("/")

VICTIMS_FILE = db_dir / 'victims.json'

def md5GUID(input_string):
    return hashlib.md5(input_string.encode('utf-8')).hexdigest()

def generate_victims_feed():
    # Load data from JSON file
    if not VICTIMS_FILE.exists():
        errlog(f"Victims file not found: {VICTIMS_FILE}")
        return

    with open(VICTIMS_FILE, encoding='utf-8') as f:
        data = json.load(f)

    # Sort data by discovered date
    data.sort(key=lambda item: datetime.strptime(item['discovered'], '%Y-%m-%d %H:%M:%S.%f'))

    # Create RSS element
    rss = Element('rss', {'version': '2.0', 'xmlns:atom': 'http://www.w3.org/2005/Atom'})

    # Create channel element
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = 'Ransomware.live RSS Feed'
    SubElement(channel, 'link').text = 'https://www.ransomware.live/rss.xml'
    SubElement(channel, 'description').text = 'Last 100 entries monitoring by Ransomware.live'

    image = SubElement(channel, 'image')
    SubElement(image, 'url').text = 'https://images.ransomware.live/ransomwarelive.png'
    SubElement(image, 'title').text = 'Ransomware.live RSS Feed'
    SubElement(image, 'link').text = 'https://www.ransomware.live/rss.xml'

    # Add atom:link element
    SubElement(channel, 'atom:link', href='https://www.ransomware.live/rss.xml', rel='self', type='application/rss+xml')

    # Iterate over last 200 items in reverse order (most recent first)
    recent_data = data[-200:]
    for item in reversed(recent_data):
        rss_item = SubElement(channel, 'item')
        item_title = SubElement(rss_item, 'title')

        item_title.text = "🏴‍☠️ " + str(item['group_name']).capitalize() + " has just published a new victim : " + str(item['post_title']).replace('&amp;', '&')
        combined_string = f"{item['post_title']}@{item['group_name']}"
        SubElement(rss_item, 'link').text  = 'https://www.ransomware.live/id/' + base64.b64encode(combined_string.encode('utf-8')).decode('utf-8')
        
        item_description = SubElement(rss_item, 'description')
        description_text = item.get('description', '')
        # SubElement will handle escaping
        item_description.text = description_text

        if item.get('post_url'):
            md5_hash = hashlib.md5(item['post_url'].encode()).hexdigest()
            image_url = f"https://images.ransomware.live/victims/{md5_hash}.png"
            image_path = home / "images" / "victims" / f"{md5_hash}.png"
            if image_path.exists():
                image_size = os.path.getsize(image_path)
                enclosure = SubElement(rss_item, 'enclosure')
                enclosure.set('url', image_url)
                enclosure.set('type', 'image/png')
                enclosure.set('length', str(image_size))
            else:
                image_url = "https://images.ransomware.live/ransomwarelive.png"
                image_path = home / "images" / "ransomwarelive.png"
                if image_path.exists():
                    image_size = os.path.getsize(image_path)
                    enclosure = SubElement(rss_item, 'enclosure')
                    enclosure.set('url', image_url)
                    enclosure.set('type', 'image/png')
                    enclosure.set('length', str(image_size))
        else:
            image_url = "https://images.ransomware.live/ransomwarelive.png"
            image_path = home / "images" / "ransomwarelive.png"
            if image_path.exists():
                image_size = os.path.getsize(image_path)
                enclosure = SubElement(rss_item, 'enclosure')
                enclosure.set('url', image_url)
                enclosure.set('type', 'image/png')
                enclosure.set('length', str(image_size))
        
        item_guid = SubElement(rss_item, 'guid')
        item_guid.text = 'https://www.ransomware.live/group/' + str(item['group_name']) + '?' + md5GUID(item_title.text)
        
        country = item.get('country', 'N/A')
        category_element = SubElement(rss_item, 'category')
        category_element.text = country if country else 'N/A'
        
        date_iso = item['discovered']
        date_rfc822 = datetime.strptime(date_iso, '%Y-%m-%d %H:%M:%S.%f').strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        item_pubdate = SubElement(rss_item, 'pubDate')
        item_pubdate.text = date_rfc822

    # Ensure data_dir exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert RSS object to string and save to file
    rss_str = tostring(rss, encoding='unicode')
    with open(data_dir / 'rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss_str)
    stdlog('Victims Feed : generated')


def generate_cyberattacks_feed():
    # URL containing the JSON data
    url = 'https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/cyberattacks.json'

    # Fetch data from the URL
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        errlog(f"Failed to fetch cyberattacks data: {e}")
        return

    # Load JSON data
    json_data = response.json()

    # Sort items by date
    sorted_data = sorted(json_data, key=lambda x: x['date'], reverse=True)[:100]

    # Create the XML structure
    rss = Element('rss', {'version': '2.0', 'xmlns:atom': 'http://www.w3.org/2005/Atom'})
    channel = SubElement(rss, 'channel')

    # Add Channel info
    SubElement(channel, 'title').text = "Ransomware.live: Last Cyber attacks Feed"
    SubElement(channel, 'link').text = "https://www.ransomware.live/recentcyberattacks"
    SubElement(channel, 'description').text = "Last 100 cyber attacks monitoring by Ransomware.live"

    # Add Channel image
    image = SubElement(channel, 'image')
    SubElement(image, 'url').text = "https://www.ransomware.live/ransomwarelive.png"
    SubElement(image, 'title').text = "Ransomware.live: Last Cyber attacks Feed"
    SubElement(image, 'link').text = "https://www.ransomware.live/recentcyberattacks"

    # Add atom:link element
    SubElement(channel, 'atom:link', href='https://www.ransomware.live/cyberattacks.xml', rel='self', type='application/rss+xml')

    # Add RSS elements for each sorted item
    for item in sorted_data:
        try:
            rss_item = SubElement(channel, 'item')
            SubElement(rss_item, 'title').text = item['title'] + ' ('+ item['country'] + ')'
            SubElement(rss_item, 'description').text = '(' + item['domain'] + ') ' + item['summary']
            combined_string = f"{item['domain']}@{item['date']}"
            link_encoded = base64.b64encode(combined_string.encode('utf-8')).decode('utf-8')
            SubElement(rss_item, 'link').text = 'https://www.ransomware.live/press#' + link_encoded

            # Convert date to RFC-822 format with GMT timezone
            date_str = item['date']
            datetime_obj = datetime.strptime(date_str, '%Y-%m-%d')
            datetime_obj = pytz.utc.localize(datetime_obj)
            rfc_822_date = datetime_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
            SubElement(rss_item, 'pubDate').text = rfc_822_date

            item_guid = SubElement(rss_item, 'guid')
            item_guid.text = 'https://www.ransomware.live/?=' + md5GUID(item['title'])
        except Exception as e:
            errlog(f"Error processing item '{item.get('title')}': {e}")

    # Ensure data_dir exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create an ElementTree object and write to the file
    file_path = data_dir / 'cyberattacks.xml'
    tree = ElementTree(rss)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    stdlog('Cyber attacks Feed : generated')

def main():
    parser = argparse.ArgumentParser(description="Generate RSS feeds for Ransomware.live")
    parser.add_argument("-V", "--victims", action="store_true", help="Generate victims RSS feed")
    parser.add_argument("-C", "--cyberattacks", action="store_true", help="Generate cyberattacks RSS feed")
    parser.add_argument("-A", "--all", action="store_true", help="Generate all RSS feeds")
    
    args = parser.parse_args()
    
    if args.all or args.victims:
        generate_victims_feed()
    if args.all or args.cyberattacks:
        generate_cyberattacks_feed()
    
    if not (args.all or args.victims or args.cyberattacks):
        parser.print_help()

if __name__ == "__main__":
    main()


