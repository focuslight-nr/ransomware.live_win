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
│   ├── _parsers/         # 140以上のサイト別パーサー
│   ├── _tools/           # 補助ツールとユーティリティスクリプト
│   ├── batch_add_groups.py # 外部ソースからランサムウェアグループを一括追加
│   ├── check_tmp_errors.py # スクレイピング済みファイルの接続エラーを特定
│   ├── export_to_excel.py # データを Excel 形式にエクスポート
│   ├── hudsonrockapi.py  # Hudson Rock APIとの連携
│   ├── libcapture.py     # サイトキャプチャ用コアライブラリ
│   ├── list_failures.py  # スクレイピングに失敗したグループを一覧表示
│   ├── list_scrape_success.py # スクレイピングに成功したグループを一覧表示
│   ├── manage.py         # 被害者/グループ管理用CLI
│   ├── mass_capture.py   # 全被害者のスクリーンショットを一括キャプチャ
│   ├── parse.py          # 収集したデータを構造化フォーマットに解析
│   ├── rsslib.py         # RSSフィード生成ライブラリ
│   ├── scrape.py         # メインのスクレイピングエンジン
│   ├── shared_utils.py   # 共有ヘルパー関数とロギング
│   ├── status.py         # システムヘルスとプロセスステータス
│   └── victims-browser.py# 対話型ターミナルブラウザ (TUI)
│
├── db/                   # ローカルデータベース (JSON)
├── images/               # スクリーンショットとアイコン
├── tmp/                  # 一時作業ファイル
├── .env.sample           # 環境設定のサンプル
├── requirements.txt      # コア依存関係
└── requirements-windows.txt # Windows固有の依存関係
```

---

## 🚀 使用方法

### 🕸️ 基本ワークフロー

1.  **スクレイピングの開始**:
    ランサムウェアのリークサイトから `tmp/` ディレクトリにページをダウンロードします。Tor を使用して `.onion` サイトにアクセスし、AI によるキャプチャ突破もサポートしています。
    ```bash
    python bin/scrape.py [OPTIONS]
    ```
    **利用可能なオプション:**
    - `-G, --group NAME`: 特定のグループのみをスクレイピングします。
    - `-B, --bypass`: データベースで `enabled: false` に設定されているグループも含め、すべてスクレイピングします。
    - `-F, --force`: `scrape.lock` ファイルを削除し、即座にスクレイピングを開始します。
    - `-V, --verbose`: 詳細な接続ログと進捗を表示します。

2.  **収集したデータの解析**:
    `tmp/` 内のファイルをサイト別のロジックで処理し、JSON データベースを更新します。
    ```bash
    python bin/parse.py [OPTIONS]
    ```
    **利用可能なオプション:**
    - `-G, --group NAME`: 特定のパーサーのみを実行します（例: `python bin/parse.py -G lockbit`）。
    - `-F, --force`: `parse.lock` ファイルを削除し、即座に解析を開始します。

3.  **結果の閲覧 (TUI)**:
    対話的なターミナルインターフェースを開き、被害者データの表示、フィルタリング、編集を行います。
    ```bash
    python bin/victims-browser.py
    ```

### 🛠️ 管理とメンテナンス

- **システムステータスとクリーンアップ**:
    必要なディレクトリの存在確認や Tor の動作確認を行います。`--clean` を付けると `tmp/` ディレクトリを空にします。
    ```bash
    python bin/status.py [--clean]
    ```

- **管理用 CLI**:
    コマンドラインからグループや被害者の追加、編集、削除を行います。
    ```bash
    python bin/manage.py [OPTIONS]
    ```

    **利用可能なオプション:**
    - `-A, --add NAME LOCATION`: 新しいグループを追加、または既存のグループに新しい URL を追加します。
      *例:* `python bin/manage.py -A "lockbit" "http://lockbitapt2xf.onion"`
    - `-U, --append NAME LOCATION`: **既存の**グループに新しい URL を追加します（グループが存在しない場合はエラーになります）。
    - `-B, --blur PATH`: スクリーンショットにガウスぼかしを適用します（元の画像は `-ORIG.png` として保存されます）。
      *例:* `python bin/manage.py -B images/victims/target.png`
    - `-I, --infostealer DOMAIN`: 指定したドメインに関連するインフォスティーラー情報を Hudson Rock API で照会します。
      *例:* `python bin/manage.py -I example.com`
    - `-P, --purge`: `tmp/` ディレクトリ内の 24 時間以上経過したキャッシュ用 `.html` ファイルを削除します。
    - `-F, --force`: 前回のプロセスが異常終了した場合などに残る `scrape.lock` ファイルを強制的に削除します。



- **データのエクスポート**:
    被害者とグループのデータを `victims.xlsx` と `groups.xlsx` に保存します。
    ```bash
    python bin/export_to_excel.py
    ```

### 📸 スクリーンショットのキャプチャ

- **被害者の一括キャプチャ**:
    すべての被害者ページのスクリーンショットを自動的に撮影します。
    ```bash
    python bin/mass_capture.py
    ```

### 🔍 診断とトラブルシューティング

- **スクレイピングエラーの確認**:
    ネットワークエラー（「Server Not Found」など）で失敗したグループを特定します。
    ```bash
    python bin/check_tmp_errors.py
    ```

- **成功したスクレイピングの一覧**:
    前回の実行で正常にダウンロードされたすべてのグループを表示します。
    ```bash
    python bin/list_scrape_success.py
    ```

- **スクレイピング失敗の特定**:
    現在スクレイピングに失敗しているグループを一覧表示します。
    ```bash
    python bin/list_failures.py
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

`.env.sample` を `.env` にコピーして、APIキーやパスを設定してください。

```bash
cp .env.sample .env
```

### 📝 環境変数の詳細説明

#### 🏠 基本設定
- `RANSOMWARELIVE_HOME`: プロジェクトのルートディレクトリ (デフォルト: `.`)。
- `DB_DIR`: JSONデータベースの保存先 (デフォルト: `/db/`)。
- `IMAGES_DIR`: サイトのファビコンや画像の保存先 (デフォルト: `/images/`)。
- `TMP_DIR`: スクレイピング時の一時HTMLファイルの保存先 (デフォルト: `/tmp/`)。
- `DATA_DIR`: 追加データの保存先 (デフォルト: `/data/`)。
- `TOR_PROXY_SERVER`: TorプロキシのURL (デフォルト: `socks5://127.0.0.1:9050`)。

#### 🕷️ スクレイピングとブラウザ
- `SCRAPE_CONCURRENCY`: 同時スクレイピング数。Tor環境では `1` が最も安定します。
- `PLAYWRIGHT_BROWSER`: 使用するブラウザエンジン (`firefox`, `chromium`, または `webkit`)。Tor経由では Firefox が推奨されます。

#### 🤖 AI関連機能
- `AI_PROVIDER`: 使用するAIプロバイダー (`openai`, `gemini`, または `anthropic`)。
- `AI_ENRICHMENT_ENABLED`: `true` に設定すると、AIを使用して被害者の業種や国を自動分類します。
- `AI_CAPTCHA_SOLVING_ENABLED`: `true` に設定すると、AI Visionを使用してスクレイピング中の画像キャプチャを自動突破します。

**プロバイダー別の設定:**
- `OPENAI_API_KEY` / `OPENAI_MODEL`: OpenAIのAPIキーとモデル名 (例: `gpt-4o`)。
- `GEMINI_API_KEY` / `GEMINI_MODEL`: Google GeminiのAPIキーとモデル名 (例: `models/gemini-2.5-flash`)。
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`: Anthropic ClaudeのAPIキーとモデル名 (例: `claude-3-5-sonnet-20241022`)。

#### 📸 スクリーンショットとウォーターマーク
- `AUTO_SCREENSHOT_VICTIMS`: 新しい被害者が追加された際に自動的にスクリーンショットを撮影します。
- `AUTO_SCREENSHOT_GROUPS`: スクレイピング中にリークサイトのインデックスページを撮影します。
- `USE_WATERMARK`: キャプチャした画像にウォーターマークを付与します。
- `WATERMARK_IMAGE_PATH`: ウォーターマーク画像のパス (`RANSOMWARELIVE_HOME` からの相対パス)。
- `SCREENSHOT_DIR`: スクリーンショットの保存先 (デフォルト: `/images/screenshots/`)。

#### 🧅 Tor 管理 (Windows)
- `TOR_AUTO_MANAGE`: `true` に設定すると、スクリプト実行時に Tor を自動的に起動・終了します。
- `TOR_BINARY_PATH`: Tor 実行ファイルの絶対パス (例: `C:\tor\tor.exe`)。
- `TOR_PASSWORD`: Tor のコントロールポート用パスワード (高度な設定が必要な場合)。
- `TOR_TORRC_PATH`: オプション。カスタム `torrc` 設定ファイルのパス。

#### 🔔 通知機能
- **Bluesky**: `BLUESKY_ENABLED`, `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`。
- **Pushover**: `PUSHOVER_ENABLED`, `PUSH_USER`, `PUSH_API`。
- **NTFY**: `NTFY_ENABLED`, `NTFY_URL`, `NTFY_TOKEN`。
- **Email**: `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_FROM`, `EMAIL_TO`。

---

### ⚠️ 対応グループと高度な解析

最新のアップデートにより、以下のような複雑なサイトもサポートしています：
- **SPA/モダンテンプレート採用サイト:** `securotrop`, `lockbit 3.0`, `shinyhunters` など。
- **AI キャプチャ突破:** `thegentlemen` (数学キャプチャを AI Vision で解決)。
- **高度なスクレイピング:** `0apt` などのグループで見られる、埋め込み JavaScript (`timelineData`) からのデータ抽出。

---


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
