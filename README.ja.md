![Ransomware.live Logo](.github/ransomware.live.png)

# Ransomware.live_win

**Ransomware.live_win** は、**Ransomware.live** (元々は **ransomwatch** のフォーク) を Windows 環境向けに最適化したフォークです。
これは、さまざまなランサムウェアのリークサイトからエントリーをスクレイピングし、公開する監視ツールです。

🔗 オリジナルのGitHubリポジトリ: [https://github.com/JMousqueton/ransomware.live](https://github.com/JMousqueton/ransomware.live)

Ransomware.live_win は、Windows システム上でのデータベース維持のために、**データ収集、解析、エンリッチメント、自動化**を処理します。

---

## 📌 主な機能

- ランサムウェアのリークサイトの**自動スクレイピング**（Tor経由での`.onion`ドメインを含む）
- Telegramボットを介したHudson Rockとの**連携**によるインフォスティーラーデータの取得
- 被害者とグループの**データ管理**ツール
- ウォーターマーク、メタデータ、オプションの顔ぼかし機能を備えたリークサイト投稿の**画像キャプチャ**
- ntfyおよびBlueskyサーバーを介した**通知機能**
- `.env`ファイルによる**環境ベースの設定**
- **Windows 最適化**: Windows のパスや環境に合わせて調整されています。

---

## 📂 リポジトリ構造

```
ransomware.live_win/
│
├── bin/                  # コアとなるPythonスクリプトとライブラリ
|   ├── _parsers/         # 各サイト用のパーサー
│   ├── libcapture.py     # 被害者/グループのスクリーンショットをキャプチャ
│   ├── mass_capture.py   # 全被害者のスクリーンショットを一括キャプチャ
│   ├── export_to_excel.py # victims.json を Excel 形式にエクスポート
│   ├── hudsonrockapi.py  # Hudson Rock APIとの連携（Telegramボット経由）
│   ├── parse.py          # 収集したデータを構造化フォーマットに解析
│   ├── scrape.py         # メインのスクレイピングエンジン
│   ├── manage.py         # 管理用CLI
│   ├── shared_utils.py   # 共有ヘルパー関数
│   ├── victims-browser.py# 被害者データビューア
│   ├── status.py         # システムヘルスとプロセスステータス
│   ├── rsslib.py         # (Optional) RSSフィード生成
│   └── requirements.txt  # Pythonの依存関係
│
├── images/               # 静的アセットとウォーターマーク
├── db/                   # ローカルデータベース (JSON)
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
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
pip install -r requirements-windows.txt
```

### 4. Playwright ブラウザのインストール
このプロジェクトではスクレイピングとスクリーンショットに Playwright を使用します。必要なブラウザバイナリ（Tor との相性が良い Firefox を推奨）をインストールしてください：
```bash
playwright install firefox
```

### 5. 環境設定
詳細は下記の **設定** セクションを参照してください。

---

## ⚙️ 設定

このプロジェクトでは、すべての設定を `.env` ファイルで管理します。

1.  **`.env` ファイルの作成:**
    ```bash
    cp .env.sample .env
    ```

2.  **`.env` ファイルの編集:**
    `.env` ファイルを開き、必要な値を設定してください。

    主要な変数:

    *   `RANSOMWARELIVE_HOME`: プロジェクトのルートディレクトリです。デフォルトは `.` で、通常はこのままで問題ありません。スクリプトを異なるディレクトリから実行する場合のみ変更してください。
    *   `T_API_ID`, `T_API_HASH`, `T_PHONE_NUMBER`: あなたのTelegram API認証情報です。`hudsonrockapi.py` がHudson Rock APIに（彼らのTelegramボット経由で）問い合わせるために使用します。
    *   `HUDSONROCK_ENABLED`: `true` または `false` を設定します。新しい被害者のWebサイトが見つかった際の、Hudson Rock APIへの自動問い合わせを有効または無効にできます。
    *   `BLUESKY_ENABLED`: `true` または `false` を設定し、Blueskyへの通知投稿を有効または無効にします。
    *   `PUSHOVER_ENABLED`: `true` または `false` を設定し、モバイルデバイスへのリアルタイムプッシュ通知を有効または無効にします。
    *   `PUSH_USER`, `PUSH_API`: Pushover の User Key と Application API Token です。
    *   `NTFY_ENABLED`: `true` または `false` を設定し、ntfy経由での通知送信を有効または無効にします。
    *   `PLAYWRIGHT_BROWSER`: Playwright で使用するブラウザの種類を設定します (`firefox`, `chromium`, `webkit`)。デフォルトは `firefox` です。
    *   `SCRAPE_CONCURRENCY`: 同時に実行するスクレイピングタスクの数（例: `1` や `3`）。デフォルトは `1` です。数値を大きくすると高速化しますが、Tor ネットワークの安定性に影響する場合があります。
    *   `TOR_AUTO_MANAGE`: `true` に設定すると、スクレイピング実行時のみ Tor プロセスを自動的に起動・終了します。
    *   `TOR_BINARY_PATH`: Tor 実行ファイルへのパス（例: `C:\Path\To\tor.exe`）。
    *   `TOR_TORRC_PATH`: (オプション) 特定の `torrc` 設定ファイルへのパス。
    *   `AUTO_SCREENSHOT_VICTIMS`: `true` に設定すると、新しい被害者が追加された際に自動でスクリーンショットを撮影します。
    *   `AUTO_SCREENSHOT_GROUPS`: `true` に設定すると、スクレイピング時にグループサイトのスクリーンショットを自動で撮影します。
    *   `USE_WATERMARK`: `true` または `false` を設定し、スクリーンショットへの透かし（ウォーターマーク）追加を有効または無効にします。
    *   `WATERMARK_IMAGE_PATH`: 透かし画像のパス（例: `/images/my-logo.png`）。
    *   その他の変数は、通知（Pushover, BlueSky, NTFY）、OpenAI, メール設定用です。

---

### ⚙️ Torの自動管理 (オプション)

Tor サービスを常にバックグラウンドで起動させておきたくない場合は、`.env` ファイルで自動管理を有効にできます：

```bash
TOR_AUTO_MANAGE=true
TOR_BINARY_PATH=C:\Path\To\tor.exe
TOR_TORRC_PATH=C:\Path\To\torrc # オプション
```

有効にすると、`scrape.py` は以下の動作を行います：
1. 起動時に新しい Tor プロセスを開始します。
2. 初期化が完了するまで待機します。
3. スクレイピングを実行します。
4. 完了時（エラー発生時を含む）に自動的に Tor プロセスを終了します。

**注意:** この機能を使用する場合、他の Tor インスタンスが同じポート（デフォルトは 9050/9051）を使用していないことを確認してください。

---

### ⚠️ 解析困難・対策が必要なグループ

以下のグループは、現在の自動スクレイピング設定や静的解析では取得に特別な工夫が必要です：

- **JavaScript / レンダリング待ち:** `cry0`, `termite`。これらの SPA サイトは、ブラウザでの完全なレンダリング完了までデータが表示されません。
- **DDoS 保護 / CAPTCHA:** `clop`。自動スクレイピングを妨げる強力な保護画面を備えています。
- **待ち行列システム:** `shinyhunters`。アクセス待ち（Access Queue）画面で止まることがあります。
- **中身が空 / オフライン:** `0x thief`, `abrahams ax` など。サイト自体がダウンしている場合に発生します。

*※ `thegentlemen` などの数学キャプチャ採用サイトは、AI（Gemini/OpenAI）による自動突破が可能になりました。*
*※ `securotrop`, `kairos`, `killsecurity3.0`, `linkc`, `genesis`, `termite` などの SPA/モダンテンプレート採用サイトについては、最新のアップデートにより自動解析・レンダリング待ちが可能になりました。*

---

### ⚙️ AIプロバイダーの設定

このプロジェクトは、OpenAIとGeminiのLLMを使用して、キャプチャの自動突破や被害者情報の自動補完が可能です。

-   `AI_PROVIDER`: 使用するAIプロバイダーを選択します。`openai` または `gemini` を設定してください。
-   `OPENAI_API_KEY` / `GEMINI_API_KEY`: 使用するプロバイダーのAPIキーを設定します。
-   `AI_CAPTCHA_SOLVING_ENABLED`: `true` に設定すると、スクレイピング時に AI Vision を使用して `thegentlemen` などの画像キャプチャを自動的に突破します（デフォルト: `false`）。
-   `AI_ENRICHMENT_ENABLED`: `true` に設定すると、取得したデータから AI が国、業種、説明文を自動的に推測・補完します（デフォルト: `true`）。

---

## 🚀 使用方法

### 監視対象グループの追加

新しいランサムウェアグループをスクレイピングする前に、システムに登録する必要があります。

1.  **`db/groups.json` の存在確認:** 初めて実行する場合、空の `groups.json` ファイルを作成する必要があるかもしれません。
    ```bash
    echo "[]" > db/groups.json
    ```

2.  **グループの追加:** `manage.py` スクリプトを使って、グループとそのリークサイトのURLを追加します。
    ```bash
    python bin/manage.py --add "GroupName" "http://group-leak-site.onion"
    ```
    `"GroupName"` をグループ名（例: "lockbit3"）に、URLをリークサイトのアドレスに置き換えてください。

**オプション: 一括追加 (試験的)**
`deepdarkCTI` などの既知のリストから、アクティブな複数のランサムウェアグループを素早く追加したい場合は、`batch_add_groups.py` スクリプトを使用できます。
```bash
python bin/batch_add_groups.py
```
*注: このスクリプトは、アクティブな .onion URL を自動的に取得し、`manage.py` を使用して追加します。追加されたグループの事後確認を推奨します。*

### スクレイピングの開始

このスクリプトは `db/groups.json` からサイトを読み込み、そのコンテンツを `/tmp` ディレクトリにダウンロードします。
```bash
python bin/scrape.py
```

### 収集したデータの解析

このスクリプトは `bin/_parsers` から適切なパーサーを見つけ、`/tmp` からダウンロードしたファイルをメインの `db/victims.json` データベースに処理します。
```bash
python bin/parse.py
```

特定のグループを解析することもできます:
```bash
python parse.py --group GroupName
```

### 稼働状況の確認 (`status.py`)

`bin/status.py`は、バックグラウンドで動作する主要なプロセス（`scrape.py`や`parse.py`）の稼働状況を監視するためのユーティリティスクリプトです。

**機能:**
- ロックファイル（`tmp/scrape.lock`, `tmp/parse.lock`）をチェックし、どのプロセスが実行中であるべきかを確認します。
- ロックファイル内のPIDを元に、プロセスが実際にアクティブかどうかを検証します。
- 実行中のスクリプトについては、稼働時間、CPU使用率、メモリ使用率などの詳細情報を表示します。
- 実行中のプロセスがないにもかかわらず残ってしまったロックファイル（孤立したロックファイル）を特定し、報告します。

**使用方法:**
ステータスを確認する場合:
```shell
python bin/status.py
```

孤立したロックファイルを自動的にクリーンアップ（削除）する場合:
```shell
python bin/status.py --clean
```

### 対話的な被害者ブラウザ (`victims-browser.py`)

このスクリプトは、`victims.json`データベースを対話的に閲覧、フィルタリング、編集するためのターミナルベースのユーザーインターフェース（TUI）を提供します。データキュレーション（情報の整理・補完）のための強力なツールです。

**機能:**
- **2パネル表示:** 左側にスクロール可能な被害者リスト、右側に選択された被害者の詳細情報を表示します。
- **フィルタリング:** 特定のデータ（ウェブサイト、国、活動分野など）が欠けている被害者をフィルタリングし、情報を補完する必要があるレコードを簡単に見つけます。
- **検索:** `/`キーで、被害者名を対象に大文字小文字を区別しない検索を実行します。
- **編集:** 被害者の`country`（国）、`activity`（活動分野）、`website`（ウェブサイト）の各フィールドを対話的に編集できます。変更は`victims.json`に直接保存されます。
- **Infostealerチェック:** `I`キーを押すと、選択した被害者のウェブサイトに対して`manage.py`によるInfostealerチェックを起動します。
    - **注意:** この機能を利用するには、`.env`ファイルでHudson Rock連携が有効 (`HUDSONROCK_ENABLED=true`) になっており、Telegram APIの認証情報 (`T_API_ID`, `T_API_HASH`, `T_PHONE_NUMBER`) が正しく設定されている必要があります。

**使用方法:**
```shell
python bin/victims-browser.py
```

### Excelへのデータエクスポート (`export_to_excel.py`)

`victims.json` データベース全体を Excel ファイル (`victims.xlsx`) にエクスポートし、分析や報告を容易にします。

**機能:**
- JSON データをクリーンな表形式に変換します。
- リスト形式のデータ（重複情報など）をセル内の JSON 文字列として自動的に処理します。
- 重要な情報（タイトル、グループ、日付、国など）が優先されるように列を並べ替えます。

**使用方法:**
1. 依存ライブラリがインストールされていることを確認します：
   ```shell
   pip install pandas openpyxl
   ```
2. スクリプトを実行します：
   ```shell
   python bin/export_to_excel.py
   ```
   プロジェクトのルートディレクトリに `victims.xlsx` が生成されます。

### スクリーンショットの一括キャプチャ (`mass_capture.py`)

`victims.json` データベースをスキャンし、まだ保存画像が存在しない被害者のスクリーンショットを自動的に一括撮影します。

**機能:**
- **効率的:** 未撮影の被害者のみを対象にします。
- **安定:** 1件ずつ順番に処理することで、Tor ネットワークへの過負荷（接続拒否エラー等）を防ぎます。
- **Torの自動管理:** `.env` の設定に従い、実行時のみ Tor を自動起動・終了させることが可能です。

**使用方法:**
```shell
python bin/mass_capture.py
```

### RSSフィードの生成 (`rsslib.py`)

Ransomware.live Webサイト用のRSSフィード（XMLファイル）を生成します。ランサムウェア被害者情報と、最近のサイバー攻撃ニュースの2種類のフィードを作成できます。

**機能:**
- **被害者フィード:** `victims.json` から最新200件の被害者情報を含む `rss.xml` を生成します。
- **サイバー攻撃ニュースフィード:** 外部ソースからデータを取得し、最近のサイバー攻撃に関する `cyberattacks.xml` を生成します。
- **単体実行:** 手動で特定のフィードのみを更新することが可能です。

**使用方法:**
すべてのフィードを生成する場合:
```shell
python bin/rsslib.py --all
```

被害者フィードのみを生成する場合:
```shell
python bin/rsslib.py --victims
```

サイバー攻撃ニュースフィードのみを生成する場合:
```shell
python bin/rsslib.py --cyberattacks
```

### データ管理

`manage.py` スクリプトは、データベースを管理するためのいくつかのユーティリティを提供します。コマンド一覧は `python manage.py --help` で確認できます。

-   `-A` / `--add` **[グループ名] [URL]**: 新しいランサムウェアグループを監視対象として追加します。グループが既に存在する場合は、新しいURLをそのグループに追加します。
-   `-U` / `--append` **[グループ名] [URL]**: 既存のグループに新しいURLを追加します。
-   `-B` / `--blur` **[画像パス]**: 指定された画像にぼかしを適用します。
-   `-I` / `--infostealer` **[ドメイン名]**: 指定されたドメインについて、Hudson Rock APIにインフォスティーラーのデータを問い合わせます。
-   `-P` / `--purge`: 24時間以上経過した古い`.html`ファイルを一時ディレクトリから削除します。
-   `-F` / `--force`: 古いロックファイルを強制的に削除してスクリプトを実行します。

---

## 🛡️ 要件

- Python **3.9+**
- `.onion` へのアクセスのためにローカルで実行されている [Torサービス](https://www.torproject.org/)
- Telegramボットの認証情報（Hudson Rockにインフォスティーラーデータを問い合わせるために使用）
- ntfyサーバーの認証情報（通知用）
- Blueskyサーバーの認証情報（通知用）
- **Windows** (win32 環境向けに最適化)

---

## 📜 ライセンス

このプロジェクトは **unlicense** ライセンスの下でライセンスされています。
詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

## ⚠️ 免責事項

このプロジェクトは、**研究および教育目的のみ**のものです。
システムやデータへの不正アクセスのために使用しないでください。
メンテナーは、コードの誤用について一切の責任を負いません。

このプロジェクトはウェブサイトそのものではなく、解析とスクレイピングの部分のみです。

---

## 🤝 コントリビューション

コントリビューションを歓迎します！
改善提案や新機能の追加については、Issueを開くか、プルリクエストを送信してください。

### 新しいパーサーの追加

新しいランサムウェアグループのサポートを追加するには、以下の手順に従ってください:

1.  **データベースにグループを追加:** `manage.py` スクリプトを使用して、新しいグループ名とリークサイトのURLを登録します。
    ```bash
    python bin/manage.py --add "NewGroup" "http://new-group-site.onion"
    ```

2.  **パーサースクリプトの作成:**
    *   `bin/_parsers/` ディレクトリ内に新しいPythonスクリプトを作成します。
    *   **スクリプト名はグループ名と一致させる必要があります。** 例えば、グループ名が `"NewGroup"` の場合、スクリプト名は `NewGroup.py` とする必要があります。APIを使用する場合は `NewGroup-api.py` とすることもできます。
    *   スクリプトには `main()` 関数を含める必要があります。この関数が `parse.py` によって呼び出されます。
    *   `main()` 関数内に、ダウンロードされたファイルを読み込み（またはAPIから取得し）、被害者データを解析し、`shared_utils.appender()` 関数を使用してデータを保存するロジックを記述します。

---

**メンテナー:** [Julien Mousqueton](https://www.linkedin.com/in/julienmousqueton) (オリジナル)
**フォークメンテナー:** Hideyuki Shibata
**ウェブサイト:** [https://ransomware.live](https://ransomware.live)
