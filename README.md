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
|   ├── _parsers/         # 140+ site-specific parsers
│   ├── libcapture.py     # Capture victim/group screenshots
│   ├── mass_capture.py   # Bulk screenshot capture for all victims
│   ├── export_to_excel.py # Export victims/groups data to Excel format
│   ├── hudsonrockapi.py  # Hudson Rock API integration via Telegram bot
│   ├── parse.py          # Parse collected data into structured formats
│   ├── scrape.py         # Main scraping engine
│   ├── manage.py         # Management CLI
│   ├── shared_utils.py   # Shared helper functions
│   ├── victims-browser.py# Victim data viewer (TUI)
│   ├── status.py         # System health and process status
│   └── requirements.txt  # Python dependencies
│
├── db/                   # Local databases (JSON)
├── images/               # Screenshots and favicons
├── tmp/                  # Temporary working files
└── .env.sample           # Example environment configuration
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

Key variables in `.env`:

- `AI_PROVIDER`: Select `openai`, `gemini`, or `anthropic`.
- `AI_CAPTCHA_SOLVING_ENABLED`: Set to `true` to enable AI-powered captcha bypass.
- `TOR_AUTO_MANAGE`: Set to `true` to automatically manage the Tor process on Windows.
- `TOR_BINARY_PATH`: Path to your `tor.exe`.
- `SCRAPE_CONCURRENCY`: Set to `1` (safest) or higher for faster scraping.

---

### ⚠️ Supported Groups & Advanced Parsing

Thanks to recent updates, this tool now supports complex sites including:
- **SPA/Modern Templates:** `securotrop`, `kairos`, `killsecurity3.0`, `linkc`, `genesis`, `termite`, `lockbit 3.0`, and `shinyhunters`.
- **AI Captcha Bypass:** `thegentlemen` (math captchas solved via AI Vision).
- **Advanced Scraping:** Logic to extract data from embedded JavaScript (`timelineData`) as seen in groups like `0apt`.

---

## 🚀 Usage

### Start Scraping
```bash
python bin/scrape.py
```

### Parse Collected Data
```bash
python bin/parse.py
```

### Interactive Victim Browser (TUI)
Browse, filter, and edit victim data interactively:
```bash
python bin/victims-browser.py
```

### System Status & Cleanup
```bash
python bin/status.py --clean
```

### Scraping Status & Diagnostic Tools

- **Identify Connection Failures (`check_tmp_errors.py`):**
  Scans the `tmp/` directory for files containing network errors (e.g., "Server Not Found") and lists the affected groups along with their `.onion` URLs.
  ```bash
  python bin/check_tmp_errors.py
  ```
- **List Scrape Successes (`list_scrape_success.py`):**
  Identifies successfully downloaded pages in `tmp/` and displays their site titles, helping you verify which groups are currently parseable.
  ```bash
  python bin/list_scrape_success.py
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
