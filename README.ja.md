![Ransomware.live Logo](.github/ransomware.live.png)

# Ransomware.live_win

**Ransomware.live_win** は、**Ransomware.live** (元々は **ransomwatch** のフォーク) を Windows 環境向けに最適化したフォークです。
これは、さまざまなランサムウェアのリークサイトからエントリーをスクレイピングし、公開する監視ツールです。

🔗 オリジナルのGitHubリポジトリ: [https://github.com/JMousqueton/ransomware.live](https://github.com/JMousqueton/ransomware.live)

Ransomware.live_win は、Windows システム上でのデータベース維持のために、**データ収集、解析、エンリッチメント、自動化**を処理します。

---

## 📌 主な機能

- ランサムウェアのリークサイトの**自動スクレイピング**（Tor経由での`.onion`ドメインを含む）
- **140以上のランサムウェアグループ**に対応した高度な解析ロジック
- **AI を活用した強力な機能**:
    - **キャプチャ自動突破**: OpenAI または Gemini Vision を使用して、画像や数学キャプチャを自動的に解決。
    - **情報エンリッチメント**: OpenAI, Gemini, または Anthropic (Claude) を使用して、業種、国、企業説明を自動推測。
- **Windows 最適化**:
    - **Tor 自動管理**: スクレイピング実行時のみ Tor プロセスを自動的に起動・終了。
    - **堅牢なパス解決**: Windows のパス環境や CLI 実行に合わせて調整。
- Telegramボットを介したHudson Rockとの**連携**によるインフォスティーラーデータの取得
- ウォーターマーク、メタデータ、オプションの顔ぼかし機能を備えたリークサイト投稿の**画像キャプチャ**
- ntfy, Pushover, Bluesky を介した**通知機能**
- **対話的 TUI**: ターミナル上で被害者データの閲覧、検索、編集が可能。

---

## 📂 リポジトリ構造

```
ransomware.live_win/
│
├── bin/                  # コアとなるPythonスクリプトとライブラリ
|   ├── _parsers/         # 140以上のサイト別パーサー
│   ├── libcapture.py     # 被害者/グループのスクリーンショットをキャプチャ
│   ├── mass_capture.py   # 全被害者のスクリーンショットを一括キャプチャ
│   ├── export_to_excel.py # データを Excel 形式にエクスポート
│   ├── hudsonrockapi.py  # Hudson Rock APIとの連携
│   ├── parse.py          # 収集したデータを構造化フォーマットに解析
│   ├── scrape.py         # メインのスクレイピングエンジン
│   ├── manage.py         # 管理用CLI
│   ├── shared_utils.py   # 共有ヘルパー関数
│   ├── victims-browser.py# 被害者データビューア (TUI)
│   ├── status.py         # プロセスステータス監視
│   └── requirements.txt  # Pythonの依存関係
│
├── db/                   # ローカルデータベース (JSON)
├── images/               # スクリーンショットとアイコン
├── tmp/                  # 一時作業ファイル
└── .env.sample           # 環境設定のサンプル
```

---

## ⚙️ インストール

### 1. リポジトリをクローン
```bash
git clone https://github.com/focuslight-nr/ransomware.live_win.git
cd ransomware.live_win
```

### 2. 仮想環境の作成
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
pip install -r requirements-windows.txt
```

### 4. Playwright ブラウザのインストール
```bash
playwright install firefox
```

### 5. 環境設定
```bash
cp .env.sample .env
```
`.env` ファイルを編集し、APIキーやパスを設定してください。

---

## ⚙️ 設定

`.env` の主要な変数:

- `AI_PROVIDER`: `openai`, `gemini`, または `anthropic` を選択。
- `AI_CAPTCHA_SOLVING_ENABLED`: `true` に設定すると AI によるキャプチャ突破を有効化。
- `TOR_AUTO_MANAGE`: `true` に設定すると Tor プロセスを自動管理。
- `TOR_BINARY_PATH`: `tor.exe` へのパス。

---

### ⚠️ 対応グループと高度な解析

最新のアップデートにより、以下のような複雑なサイトもサポートしています：
- **SPA/モダンテンプレート採用サイト:** `securotrop`, `lockbit 3.0`, `shinyhunters` など。
- **AI キャプチャ突破:** `thegentlemen` (数学キャプチャを AI Vision で解決)。
- **高度なスクレイピング:** `0apt` などのグループで見られる、埋め込み JavaScript (`timelineData`) からのデータ抽出。

---

## 🚀 使用方法

### スクレイピングの開始
```bash
python bin/scrape.py
```

### 収集したデータの解析
```bash
python bin/parse.py
```

### 対話的な被害者ブラウザ (TUI)
被害者データの閲覧、フィルタリング、編集をターミナル上で行えます：
```bash
python bin/victims-browser.py
```

### ステータス確認とクリーンアップ
```bash
python bin/status.py --clean
```

### スクレイピング状況の診断ツール

- **接続失敗グループの特定 (`check_tmp_errors.py`):**
  `tmp/` ディレクトリ内のファイルをスキャンし、ネットワークエラー（「Server Not Found」など）が発生しているグループを、その時の `.onion` URL とともに一覧表示します。
  ```bash
  python bin/check_tmp_errors.py
  ```
- **成功グループの確認 (`list_scrape_success.py`):**
  正常にダウンロードされたページを特定し、そのサイトタイトルを表示します。現在どのグループのデータがパース可能な状態かを確認するのに役立ちます。
  ```bash
  python bin/list_scrape_success.py
  ```


---

## 📜 ライセンス

このプロジェクトは **unlicense** ライセンスの下でライセンスされています。
詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

## ⚠️ 免責事項

このプロジェクトは、**研究および教育目的のみ**のものです。
メンテナーは、コードの誤用について一切の責任を負いません。

---

**メンテナー:** [Julien Mousqueton](https://www.linkedin.com/in/julienmousqueton) (オリジナル)
**フォークメンテナー:** Hideyuki Shibata
**ウェブサイト:** [https://ransomware.live](https://ransomware.live)
