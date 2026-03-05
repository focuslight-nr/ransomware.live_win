#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging

# -------------------- ENV LOADING --------------------
script_dir = Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(dotenv_path=env_path)

home = os.getenv("RANSOMWARELIVE_HOME", ".")
db_dir = Path(home + os.getenv("DB_DIR", "/db/"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_data_for_excel(df):
    """Convert list/dict columns to strings for Excel compatibility."""
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x)
    return df

def export_victims():
    json_path = db_dir / "victims.json"
    output_file = Path(home) / "victims.xlsx"
    
    if not json_path.exists():
        logging.error(f"File not found: {json_path}")
        return

    logging.info(f"Reading {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read JSON: {e}")
        return

    if not data:
        logging.warning("No data found in victims.json")
        return

    df = pd.DataFrame(data)
    df = clean_data_for_excel(df)

    desired_order = [
        'post_title', 'group_name', 'discovered', 'published', 
        'country', 'activity', 'website', 'post_url', 'description'
    ]
    columns = [c for c in desired_order if c in df.columns] + [c for c in df.columns if c not in desired_order]
    df = df[columns]

    logging.info(f"Exporting victims to {output_file}...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    logging.info("Success!")

def export_groups():
    json_path = db_dir / "groups.json"
    output_file = Path(home) / "groups.xlsx"
    
    if not json_path.exists():
        logging.error(f"File not found: {json_path}")
        return

    logging.info(f"Reading {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read JSON: {e}")
        return

    # groups.json has a nested structure (locations list)
    # Flatten it so each location is a row
    flattened_data = []
    for group in data:
        group_info = {k: v for k, v in group.items() if k != 'locations'}
        locations = group.get('locations', [])
        
        if not locations:
            flattened_data.append(group_info)
        else:
            for loc in locations:
                row = group_info.copy()
                # Prefix location fields to avoid collision
                for k, v in loc.items():
                    row[f"loc_{k}"] = v
                flattened_data.append(row)

    df = pd.DataFrame(flattened_data)
    df = clean_data_for_excel(df)

    logging.info(f"Exporting groups to {output_file}...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    logging.info("Success!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export JSON data to Excel")
    parser.add_argument("-v", "--victims", action="store_true", help="Export victims.json to victims.xlsx")
    parser.add_argument("-g", "--groups", action="store_true", help="Export groups.json to groups.xlsx")
    args = parser.parse_args()

    if not args.victims and not args.groups:
        # Default behavior: both
        export_victims()
        export_groups()
    else:
        if args.victims:
            export_victims()
        if args.groups:
            export_groups()
