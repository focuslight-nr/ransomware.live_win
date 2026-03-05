![Ransomware.live Logo](.github/ransomware.live.png)

# Ransomware.live_win

**Ransomware.live_win** is a Windows-optimized fork of **Ransomware.live** (which is originally a fork of **ransomwatch**).
It is a ransomware leak site monitoring tool that scrapes entries from various ransomware leak sites and publishes them.

🔗 Original GitHub repository: [https://github.com/JMousqueton/ransomware.live](https://github.com/JMousqueton/ransomware.live)

Ransomware.live_win handles **data collection, parsing, enrichment, and automation** to maintain the database on Windows systems.

---

## 📌 Features

- **Automated scraping** of ransomware leak sites (including `.onion` domains via Tor)
- **Integration** with Hudson Rock for infostealer data via a Telegram bot
- **Data management** tools for victims and groups
- **Image capture** of leak site posts with watermarking, metadata, and optional face blurring
- **Notifications** via ntfy and Bluesky servers
- **Environment-based configuration** via `.env`
- **Windows Optimized**: Adjusted for Windows paths and environment.

---

## 📂 Repository Structure

```
ransomware.live_win/
│
├── bin/                  # Core Python scripts and libraries
|   ├── _parsers/         # All parsers
│   ├── libcapture.py     # Capture victim/group screenshots
│   ├── mass_capture.py   # Bulk screenshot capture for all victims
│   ├── export_to_excel.py # Export victims/groups data to Excel format
│   ├── hudsonrockapi.py  # Hudson Rock API integration via Telegram bot
│   ├── parse.py          # Parse collected data into structured formats
│   ├── scrape.py         # Main scraping engine
│   ├── manage.py         # Management CLI
│   ├── shared_utils.py   # Shared helper functions
│   ├── victims-browser.py# Victim data viewer
│   ├── status.py         # System health and process status
│   ├── rsslib.py         # (Optional) RSS feed generation
│   └── requirements.txt  # Python dependencies
│
├── db/                   # Local databases (JSON)
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
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-windows.txt
```

### 4. Install Playwright Browsers
This project uses Playwright for scraping and screenshots. You must install the required browser binaries (Firefox is recommended for Tor compatibility):
```bash
playwright install firefox
```

### 5. Configure Environment
See the **Configuration** section below for details on how to set up your `.env` file.

---

## ⚙️ Configuration

This project uses a `.env` file to manage all configuration settings.

1.  **Create the `.env` file:**
    ```bash
    cp .env.sample .env
    ```

2.  **Edit the `.env` file:**
    Open the `.env` file and fill in the required values.

    Key variables:

    *   `RANSOMWARELIVE_HOME`: The root directory of the project. It defaults to `.` which is usually correct. You should only change this if you are running the scripts from a different directory.
    *   `T_API_ID`, `T_API_HASH`, `T_PHONE_NUMBER`: Your Telegram API credentials, used by the `hudsonrockapi.py` script to query the Hudson Rock API via their Telegram bot.
    *   `HUDSONROCK_ENABLED`: Set to `true` or `false`. This allows you to enable or disable the automatic Hudson Rock API query when a new victim with a website is found.
    *   `BLUESKY_ENABLED`: Set to `true` or `false` to enable or disable posting notifications to Bluesky.
    *   `PUSHOVER_ENABLED`: Set to `true` or `false` to enable or disable real-time push notifications to your mobile device.
    *   `PUSH_USER`, `PUSH_API`: Your Pushover User Key and Application API Token.
    *   `NTFY_ENABLED`: Set to `true` or `false` to enable or disable sending notifications via ntfy.
    *   `PLAYWRIGHT_BROWSER`: Set the browser type for Playwright (`firefox`, `chromium`, or `webkit`). Defaults to `firefox`.
    *   `SCRAPE_CONCURRENCY`: Number of simultaneous scraping tasks (e.g., `1` or `3`). Default is `1`. Set higher to speed up but be careful with Tor network stability.
    *   `TOR_AUTO_MANAGE`: Set to `true` to automatically start and stop the Tor process during scraping.
    *   `TOR_BINARY_PATH`: Path to your Tor executable (e.g., `C:\Path\To\tor.exe`).
    *   `TOR_TORRC_PATH`: (Optional) Path to a specific `torrc` configuration file.
    *   `AUTO_SCREENSHOT_VICTIMS`: Set to `true` to automatically capture screenshots of victims when they are added.
    *   `AUTO_SCREENSHOT_GROUPS`: Set to `true` to automatically capture screenshots of groups during scraping.
    *   `USE_WATERMARK`: Set to `true` or `false` to enable or disable adding a watermark to screenshots.
    *   `WATERMARK_IMAGE_PATH`: Path to the watermark image (e.g., `/images/my-logo.png`).
    *   Other variables are for notifications (Pushover, BlueSky, NTFY), OpenAI, and mail settings.

---

### ⚙️ Tor Auto-Management (Experimental)

If you don't want to keep the Tor service running in the background all the time, you can enable auto-management in your `.env` file:

```bash
TOR_AUTO_MANAGE=true
TOR_BINARY_PATH=C:\Path\To\tor.exe
TOR_TORRC_PATH=C:\Path\To\torrc # Optional
```

When enabled, `scrape.py` will:
1. Start a new Tor process at launch.
2. Wait for it to initialize.
3. Perform the scraping.
4. Automatically terminate the Tor process upon completion (even if an error occurs).

**Note:** Ensure that no other Tor instance is using the same ports (default 9050/9051) if you use this feature.

---

### ⚠️ Challenging Groups & Known Issues

The following groups require special handling or are currently difficult to scrape/parse automatically:

- **JavaScript / Rendering Required:** `cry0`. These SPA sites require full browser rendering before data is visible.
- **Access Queue / DDoS Protection:** `clop`. These sites often use waiting rooms or protection screens that prevent automated scraping.
- **CAPTCHA Protected:** `kyber`, `payload`.
- **Empty / Scrape Failure:** `0x thief`, `abrahams ax`. Usually occurs when the host itself is down.
- **Access Denied:** `cloak` (403 Forbidden).
- **Seized by Law Enforcement:** `ragnar locker`, `vanir`.

*Note: Sites using math captchas like `thegentlemen` can now be automatically bypassed using AI (Gemini/OpenAI).*
*Note: Groups using modern SPA templates such as `securotrop`, `kairos`, `killsecurity3.0`, `linkc`, `genesis`, and `termite` are now supported thanks to recent parser updates.*

---

### ⚙️ AI Provider Configuration

This project can use LLMs from OpenAI and Gemini to automatically enrich information about victims, and automatically bypass certain captchas.

-   `AI_PROVIDER`: Selects the AI provider to use. Set to `openai` or `gemini`. Defaults to `openai`.
-   `OPENAI_API_KEY` / `GEMINI_API_KEY`: Set your API key for the selected provider.
-   `AI_CAPTCHA_SOLVING_ENABLED`: Set to `true` to use AI Vision to automatically solve image captchas like `thegentlemen` during scraping (default: `false`).
-   `AI_ENRICHMENT_ENABLED`: Set to `true` to use AI to automatically infer sector, description, and country from captured data (default: `true`).

---

## 🚀 Usage

### Adding a Group to Monitor

Before you can scrape a new ransomware group, you must register it in the system.

1.  **Ensure `db/groups.json` exists:** If you are running this for the first time, you may need to create an empty `groups.json` file.
    ```bash
    echo "[]" > db/groups.json
    ```

2.  **Add the group:** Use the `manage.py` script to add the group and its leak site URL.
    ```bash
    python bin/manage.py --add "GroupName" "http://group-leak-site.onion"
    ```
    Replace `"GroupName"` with the name of the group (e.g., "lockbit3") and the URL with their leak site address.

**Optional: Batch Add (Experimental)**
If you want to quickly add multiple active ransomware groups from a known list (like `deepdarkCTI`), you can use the `batch_add_groups.py` script.
```bash
python bin/batch_add_groups.py
```
*Note: This script automatically fetches active .onion URLs and adds them using `manage.py`. Manual verification of added groups is recommended.*

### Start Scraping

This script reads the sites from `db/groups.json` and downloads their content into the `/tmp` directory.
```bash
python bin/scrape.py
```

### Parse Collected Data

This script finds the appropriate parser in `bin/_parsers` and processes the downloaded files from `/tmp` into the main `db/victims.json` database.
```bash
python bin/parse.py
```

You can also parse a specific group:
```bash
python parse.py --group GroupName
```

### Checking Process Status (`status.py`)

The `bin/status.py` script is a utility to monitor the status of the main background processes (`scrape.py` and `parse.py`).

**Features:**
- Checks for lock files (`tmp/scrape.lock`, `tmp/parse.lock`) to see which processes should be running.
- Uses the PID from the lock file to verify if the process is currently active.
- Displays process details for running scripts, including uptime, CPU usage, and memory usage.
- Identifies and reports orphan lock files (i.e., lock files without a corresponding running process).

**Usage:**
To check the status:
```shell
python bin/status.py
```

To automatically clean up orphan lock files:
```shell
python bin/status.py --clean
```

### Interactive Victim Browser (`victims-browser.py`)

This script provides a terminal-based user interface (TUI) for interactively browsing, filtering, and editing the `victims.json` database. It is a powerful tool for data curation.

**Features:**
- **Two-Panel View:** Displays a scrollable list of victims on the left and detailed information for the selected victim on the right.
- **Filtering:** Filter victims that are missing specific data (e.g., website, country, or activity type) to easily find records that need enrichment.
- **Search:** Use `/` to perform a case-insensitive search for victims by name.
- **Editing:** Interactively edit the `country`, `activity`, and `website` fields for any victim. Changes are saved directly to `victims.json`.
- **Infostealer Check:** Press `I` to launch the `manage.py` infostealer check for the selected victim's website.
    - **Note:** This feature requires the Hudson Rock integration to be enabled (`HUDSONROCK_ENABLED=true`) and the Telegram API credentials (`T_API_ID`, `T_API_HASH`, `T_PHONE_NUMBER`) to be correctly configured in your `.env` file.

**Usage:**
```shell
python bin/victims-browser.py
```

### Exporting Data to Excel (`export_to_excel.py`)

This script exports the collected data from JSON files into Excel format for easier analysis and reporting.

**Features:**
- Converts JSON data into a clean, tabular format.
- Automatically handles list-type data (like duplicates) by converting them to JSON strings within cells.
- **Groups Export:** Flattens the nested `locations` list so each site/mirror is a separate row.
- Reorders columns to prioritize key information.

**Usage:**
1. Ensure dependencies are installed:
   ```shell
   pip install pandas openpyxl
   ```
2. Run the script:
   - **Export both Victims and Groups:**
     ```shell
     python bin/export_to_excel.py
     ```
   - **Export only Victims (`victims.xlsx`):**
     ```shell
     python bin/export_to_excel.py --victims
     ```
   - **Export only Groups (`groups.xlsx`):**
     ```shell
     python bin/export_to_excel.py --groups
     ```

### Bulk Screenshot Capture (`mass_capture.py`)

This script scans the `victims.json` database and automatically captures screenshots for any victims that do not yet have a corresponding image in the storage directory.

**Features:**
- **Efficient:** Only captures missing screenshots.
- **Stable:** Processes victims one by one to avoid overloading the Tor network.
- **Managed Tor:** Supports automatic Tor startup/shutdown (if enabled in `.env`).

**Usage:**
```shell
python bin/mass_capture.py
```

### RSS Feed Generation (`rsslib.py`)

This script generates RSS feeds (XML files) for the Ransomware.live website. It can generate feeds for both ransomware victims and recent cyber attack news.

**Features:**
- **Victims Feed:** Generates `rss.xml` from the `victims.json` database, including the 200 most recent victims with links and image enclosures.
- **Cyber Attacks Feed:** Generates `cyberattacks.xml` by fetching data from external cyber attack monitoring sources.
- **Stand-alone Execution:** Can be run manually to update specific feeds.

**Usage:**
To generate both feeds:
```shell
python bin/rsslib.py --all
```

To generate only the victims feed:
```shell
python bin/rsslib.py --victims
```

To generate only the cyber attacks feed:
```shell
python bin/rsslib.py --cyberattacks
```

### Manage Data

The `manage.py` script provides several utilities for managing the database. You can see the full list of commands by running `python manage.py --help`.

-   `-A` / `--add` **[NAME] [LOCATION]**: Adds a new ransomware group to be monitored. If the group already exists, it appends the new location to it.
-   `-U` / `--append` **[NAME] [LOCATION]**: Appends a new location to an existing group.
-   `-B` / `--blur` **[PATH]**: Applies a blur effect to the specified image file.
-   `-I` / `--infostealer` **[DOMAIN]**: Performs an infostealer query for the specified domain against the Hudson Rock API.
-   `-P` / `--purge`: Deletes all `.html` files in the temporary directory that are older than 24 hours.
-   `-F` / `--force`: Forces the removal of a stale lock file before running a command.

---

## 🛡️ Requirements

- Python **3.9+**
- [Tor service](https://www.torproject.org/) running locally for `.onion` access
- Telegram bot credentials (used to query Hudson Rock for infostealer data)
- ntfy server credentials (for notifications)
- Bluesky server credentials (for notifications)
- **Windows** (Optimized for win32 environment)

---

## 📜 License

This project is licensed under the **unlicense** License**.
See the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This project is for **research and educational purposes only**.
Do **not** use it for unauthorized access to systems or data.
The maintainers take no responsibility for misuse of the code.

This project is only the parsing and scraping, not the website.

---

## 🤝 Contributing

Contributions are welcome!
Please open an issue or submit a pull request to suggest improvements or add new features.

### Adding a New Parser

To add support for a new ransomware group, follow these steps:

1.  **Add the Group to the Database:** Use the `manage.py` script to register the new group's name and leak site URL.
    ```bash
    python bin/manage.py --add "NewGroup" "http://new-group-site.onion"
    ```

2.  **Create the Parser Script:**
    *   Create a new Python script inside the `bin/_parsers/` directory.
    *   **The script must be named after the group.** For example, if the group is named `"NewGroup"`, the script must be named `NewGroup.py`. If it uses an API, you can name it `NewGroup-api.py`.
    *   The script must contain a `main()` function, which will be called by `parse.py`.
    *   Inside the `main()` function, write the logic to read the downloaded file (or fetch from an API), parse the victim data, and use the `shared_utils.appender()` function to save the data.

---

**Maintainer:** [Julien Mousqueton](https://www.linkedin.com/in/julienmousqueton) (Original)
**Fork Maintainer:** Hideyuki Shibata
**Website:** [https://ransomware.live](https://ransomware.live)
