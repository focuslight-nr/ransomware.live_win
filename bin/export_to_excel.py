#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import logging

# -------------------- ENV LOADING --------------------
script_dir = Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(dotenv_path=env_path)

home = os.getenv("RANSOMWARELIVE_HOME", ".")
db_dir = Path(home + os.getenv("DB_DIR", "/db/"))
output_file = Path(home) / "victims.xlsx"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def export_victims_to_excel():
    json_path = db_dir / "victims.json"
    
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

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # データの整理 (読みやすくするための処理)
    # リスト形式のデータ（duplicatesやextrainfos）を文字列に変換してExcelで表示可能にする
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)

    # 列の順番を整理（使いやすい順に）
    desired_order = [
        'post_title', 'group_name', 'discovered', 'published', 
        'country', 'activity', 'website', 'post_url', 'description'
    ]
    # 存在する列のみで並び替え
    columns = [c for c in desired_order if c in df.columns] + [c for c in df.columns if c not in desired_order]
    df = df[columns]

    logging.info(f"Exporting to {output_file}...")
    try:
        # Excelとして保存
        # エンジンに openpyxl を使用。列幅の自動調整などは pandas の標準機能にはないため、
        # 必要であれば保存後に openpyxl で調整可能ですが、まずはシンプルな出力を行います。
        df.to_excel(output_file, index=False, engine='openpyxl')
        logging.info("Success! The Excel file has been created.")
    except Exception as e:
        logging.error(f"Failed to export Excel: {e}")

if __name__ == "__main__":
    export_victims_to_excel()
