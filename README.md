![Ransomware.live Logo](.github/ransomware.live.png)

# Ransomware.live_win

**Ransomware.live_win** is a Windows-optimized fork of **Ransomware.live** (originally a fork of **ransomwatch**).
It is a ransomware leak site monitoring tool that scrapes entries from various ransomware leak sites and publishes them.

🔗 Original GitHub repository: [https://github.com/JMousqueton/ransomware.live](https://github.com/JMousqueton/ransomware.live)

Ransomware.live_win handles **data collection, parsing, enrichment, and automation** to maintain the database on Windows systems.

---

## 📌 Features

- **Automated scraping** of ransomware leak sites (including `.onion` domains via Tor)
- **Support for 140+ ransomware groups** with advanced parsing logic
- **AI-Powered Capabilities**:
    - **CAPTCHA Solving**: Automatically bypass image/math captchas using OpenAI or Gemini Vision.
    - **Data Enrichment**: Automatically infer industry sector, country, and company description using OpenAI, Gemini, or Anthropic (Claude).
- **Windows Optimized**:
    - **Auto Tor Management**: Automatically start and stop the Tor process during scraping.
    - **Robust Path Resolution**: Designed to work reliably on Windows/CLI environments.
- **Integration** with Hudson Rock for infostealer data via a Telegram bot
- **Image capture** of leak site posts with watermarking, metadata, and optional face blurring
- **Notifications** via ntfy, Pushover, and Bluesky
- **Interactive TUI**: Browse and edit victim data directly in your terminal

---

## 📂 Repository Structure

```
ransomware.live_win/
│
├── bin/                  # Core Python scripts and libraries
│   ├── _parsers/         # 140+ site-specific parsers
│   ├── _tools/           # Auxiliary tools and utility scripts
│   ├── batch_add_groups.py # Batch add new ransomware groups from external source
│   ├── check_tmp_errors.py # Identify connection failures in scraped files
│   ├── export_to_excel.py # Export victims/groups data to Excel format
│   ├── hudsonrockapi.py  # Hudson Rock API integration via Telegram bot
│   ├── libcapture.py     # Core library for site screenshots
│   ├── list_failures.py  # List groups that failed to scrape
│   ├── list_scrape_success.py # List successfully scraped groups
│   ├── manage.py         # Management CLI for victims and groups
│   ├── mass_capture.py   # Bulk screenshot capture for all victims
│   ├── parse.py          # Parse collected data into structured formats
│   ├── rsslib.py         # RSS feed generation library
│   ├── scrape.py         # Main scraping engine
│   ├── shared_utils.py   # Shared helper functions and logging
│   ├── status.py         # System health and process status
│   └── victims-browser.py# Interactive terminal browser (TUI)
│
├── db/                   # Local databases (JSON)
├── images/               # Screenshots and favicons
├── tmp/                  # Temporary working files
├── .env.sample           # Example environment configuration
├── requirements.txt      # Core dependencies
└── requirements-windows.txt # Windows-specific dependencies
```

---

## 🚀 Usage Guide

### 🕸️ Core Workflow

1.  **Start Scraping**:
    Downloads pages from ransomware leak sites to the `tmp/` directory. Uses Tor for `.onion` sites and supports AI-powered CAPTCHA solving.
    ```bash
    python bin/scrape.py [OPTIONS]
    ```
    **Available Options:**
    - `-G, --group NAME`: Scrape only a specific group.
    - `-B, --bypass`: Scrape all groups, even those marked as `enabled: false` in the database.
    - `-F, --force`: Remove `scrape.lock` and start scraping immediately.
    - `-V, --verbose`: Show detailed connection logs and scraping progress.

2.  **Parse Collected Data**:
    Processes files in `tmp/` using site-specific logic and updates the JSON databases.
    ```bash
    python bin/parse.py [OPTIONS]
    ```
    **Available Options:**
    - `-G, --group NAME`: Run a specific parser (e.g., `python bin/parse.py -G lockbit`).
    - `-F, --force`: Remove `parse.lock` and start parsing immediately.

3.  **Browse Results (TUI)**:
    Open an interactive terminal interface to view, filter, and edit victim data.
    ```bash
    python bin/victims-browser.py
    ```

### 🛠️ Management & Maintenance

- **System Status & Cleanup**:
    Check if the required directories exist and Tor is running. Use `--clean` to empty the `tmp/` directory.
    ```bash
    python bin/status.py [--clean]
    ```

- **Management CLI**:
    Add, edit, or remove groups and victims via command line.
    ```bash
    python bin/manage.py [OPTIONS]
    ```

    **Available Options:**
    - `-A, --add NAME LOCATION`: Add a new group or append a new URL to an existing group.
      *Example:* `python bin/manage.py -A "lockbit" "http://lockbitapt2xf.onion"`
    - `-U, --append NAME LOCATION`: Append a new URL to an **existing** group.
    - `-B, --blur PATH`: Apply a Gaussian blur effect to a screenshot (original is saved with `-ORIG.png`).
      *Example:* `python bin/manage.py -B images/victims/target.png`
    - `-I, --infostealer DOMAIN`: Query Hudson Rock API for infostealer data related to a domain.
      *Example:* `python bin/manage.py -I example.com`
    - `-P, --purge`: Delete all cached `.html` files in the `tmp/` directory older than 24 hours.
    - `-F, --force`: Forcefully remove the `scrape.lock` file if a previous scrape crashed.



- **Export Data**:
    Save victim and group data into `victims.xlsx` and `groups.xlsx`.
    ```bash
    python bin/export_to_excel.py
    ```

### 📸 Screenshot Capture

- **Bulk Capture Victims**:
    Automatically take screenshots of all victim pages.
    ```bash
    python bin/mass_capture.py
    ```

### 🔍 Diagnostics & Troubleshooting

- **Check Scraping Errors**:
    Identify groups that failed due to network errors (e.g., "Server Not Found").
    ```bash
    python bin/check_tmp_errors.py
    ```

- **List Successful Scrapes**:
    List all groups that were successfully downloaded during the last run.
    ```bash
    python bin/list_scrape_success.py
    ```

- **List Scraping Failures**:
    Identify groups that are currently failing to scrape.
    ```bash
    python bin/list_failures.py
    ```

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/focuslight-nr/ransomware.live_win.git
cd ransomware.live_win
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-windows.txt
```

### 4. Install Playwright Browsers
```bash
playwright install firefox
```

### 5. Configure Environment
```bash
cp .env.sample .env
```
Edit `.env` and fill in your API keys and paths.

---

## ⚙️ Configuration

Copy `.env.sample` to `.env` and fill in your API keys and paths.

```bash
cp .env.sample .env
```

### 📝 Detailed Environment Variables

#### 🏠 Core Configuration
- `RANSOMWARELIVE_HOME`: Root directory of the project (default: `.`).
- `DB_DIR`: Directory where JSON databases are stored (default: `/db/`).
- `IMAGES_DIR`: Directory for storing site favicons and images (default: `/images/`).
- `TMP_DIR`: Directory for temporary HTML files during scraping (default: `/tmp/`).
- `DATA_DIR`: Directory for additional data (default: `/data/`).
- `TOR_PROXY_SERVER`: URL of the Tor proxy (default: `socks5://127.0.0.1:9050`).

#### 🕷️ Scraping & Browsing
- `SCRAPE_CONCURRENCY`: Number of simultaneous scraping tasks. Set to `1` for maximum reliability on Tor.
- `PLAYWRIGHT_BROWSER`: Browser engine to use (`firefox`, `chromium`, or `webkit`). Firefox is generally most stable with Tor.

#### 🤖 AI-Powered Features
- `AI_PROVIDER`: Choose your primary AI backend (`openai`, `gemini`, or `anthropic`).
- `AI_ENRICHMENT_ENABLED`: If `true`, uses AI to automatically categorize victims by sector and country.
- `AI_CAPTCHA_SOLVING_ENABLED`: If `true`, uses AI Vision to solve image-based CAPTCHAs during scraping.

**Provider Specifics:**
- `OPENAI_API_KEY` / `OPENAI_MODEL`: API key and model (e.g., `gpt-4o`) for OpenAI.
- `GEMINI_API_KEY` / `GEMINI_MODEL`: API key and model (e.g., `models/gemini-2.5-flash`) for Google Gemini.
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`: API key and model (e.g., `claude-3-5-sonnet-20241022`) for Anthropic Claude.

#### 📸 Screenshots & Watermarking
- `AUTO_SCREENSHOT_VICTIMS`: Automatically capture a screenshot when a new victim is added.
- `AUTO_SCREENSHOT_GROUPS`: Capture a screenshot of the leak site index during scraping.
- `USE_WATERMARK`: Apply a watermark to captured screenshots.
- `WATERMARK_IMAGE_PATH`: Path to the watermark image (relative to `RANSOMWARELIVE_HOME`).
- `SCREENSHOT_DIR`: Path where screenshots are saved (default: `/images/screenshots/`).

#### 🧅 Tor Management (Windows)
- `TOR_AUTO_MANAGE`: If `true`, the script will start/stop Tor automatically.
- `TOR_BINARY_PATH`: Absolute path to the Tor executable (e.g., `C:\tor\tor.exe`).
- `TOR_PASSWORD`: Control port password for Tor (required for some advanced features).
- `TOR_TORRC_PATH`: Optional path to a custom `torrc` configuration file.

#### 🔔 Notifications
- **Bluesky**: `BLUESKY_ENABLED`, `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`.
- **Pushover**: `PUSHOVER_ENABLED`, `PUSH_USER`, `PUSH_API`.
- **NTFY**: `NTFY_ENABLED`, `NTFY_URL`, `NTFY_TOKEN`.
- **Email**: `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_FROM`, `EMAIL_TO`.

---

### ⚠️ Supported Groups & Advanced Parsing

Thanks to recent updates, this tool now supports complex sites including:
- **SPA/Modern Templates:** `securotrop`, `kairos`, `killsecurity3.0`, `linkc`, `genesis`, `termite`, `lockbit 3.0`, and `shinyhunters`.
- **AI Captcha Bypass:** `thegentlemen` (math captchas solved via AI Vision).
- **Advanced Scraping:** Logic to extract data from embedded JavaScript (`timelineData`) as seen in groups like `0apt`.

---

## 🖥️ GUI Tool

A local web-based GUI for browsing and managing the JSON databases, running scrape/parse jobs, and viewing threat intelligence dashboards.

### Features

| Tab | What you can do |
|-----|----------------|
| **Dashboard** | Overview stats, top groups by victim count, country & sector distribution, recently discovered victims |
| **Groups** | Browse/search all 256+ groups; click any row to open the edit panel |
| **Groups – edit** | Update date / meta / description / contact; add or remove locations (URLs); Save creates a timestamped `.bak` backup automatically |
| **Victims** | Paginated searchable table; filter by group, country, sector; click ✏️ to edit country / website / sector / description |
| **Run Scrape/Parse** | Pick a group, choose Scrape or Parse, click Run — live log streams in the output box; job history retained in sidebar |

### Requirements

`aiohttp` is already included in the `.venv`. No additional packages needed.

### Launch

**macOS / Linux**
```bash
./start-gui.sh
# or with options:
./start-gui.sh --port 8080 --no-browser
```

**Windows**
```bat
start-gui.bat
:: or:
start-gui.bat --port 8080 --no-browser
```

**Direct (any platform)**
```bash
.venv/bin/python3 gui.py          # macOS/Linux
.venv\Scripts\python.exe gui.py   # Windows
```

The GUI opens at **http://localhost:8080** in your default browser.

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--port N` | `8080` | Port to listen on |
| `--no-browser` | off | Don't open the browser automatically |
| `--no-fallback` | off | Exit with an error if the port is busy (instead of auto-switching) |

### Port conflict behaviour

If the requested port is already in use, the GUI automatically finds the next available port (up to +10) and prints a warning:

```
[WARN] Port 8080 is already in use — switching to port 8081.
```

To force a hard failure instead (useful in scripts):

```bash
./start-gui.sh --no-fallback
```

To manually free port 8080:

```bash
# macOS / Linux
lsof -ti tcp:8080 | xargs kill

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess | Stop-Process
```

---

## 📜 License

This project is licensed under the **unlicense** License.
See the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This project is for **research and educational purposes only**.
The maintainers take no responsibility for misuse of the code.

---

**Maintainer:** [Julien Mousqueton](https://www.linkedin.com/in/julienmousqueton) (Original)
**Fork Maintainer:** Hideyuki Shibata
**Website:** [https://ransomware.live](https://ransomware.live)
