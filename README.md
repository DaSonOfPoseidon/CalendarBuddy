# CalendarBuddy Launcher — Centralized GUI and Updater for Internal Automation Tools

A centralized graphical launcher and updater designed to efficiently manage internal automation tools within a corporate environment.

---

## Overview

CalendarBuddy provides a simple graphical interface to manage and launch several internal automation tools, including:

- **ASSigner** — Automated job assignment tool  
- **JobScraper** — Job calendar scraper and updater  
- **ButterKnife** — Job spreader/reassignment tool  
- **ConsultationCrusher** — Consultation task processor  

---

## Features

- **Unified GUI Launcher** — Launch all internal automation tools from a single, easy-to-use interface.  
- **Centralized Credential Management** — Securely configure and store credentials and email recipients in a local `.env` file via the launcher UI.  
- **Automated Environment Setup** — Ships only the launcher executable, which downloads required dependencies, interpreters, and app binaries on demand.  
- **CI/CD Friendly Update Process** — Updates are managed externally via GitHub Actions and Releases and applied by the launcher using an external `Updater.exe` helper executable.  
- **Detailed Logging** — Each app logs to dedicated files under a centralized `logs` folder for easy auditing and troubleshooting.  
- **Optional GitHub Token Support** — For authenticated API requests to mitigate rate limiting on update checks.

---

## Typical Workflow

1. **Launch CalendarBuddy**  
   - Opens a window with buttons to launch each managed tool.  
   - Displays current credential and email recipient settings.

2. **Configure Settings**  
   - Enter or update your internal credentials and recipient emails.  
   - Save settings to the `.env` file for persistent use.

3. **Run Automation Apps**  
   - Click on any tool’s button (e.g., "Run Scraper") to launch the corresponding executable.  
   - The launcher automatically downloads or updates executables as needed.  
   - If an update is available, it will be applied before launching.

4. **View Logs**  
   - Each app writes logs to the `logs` directory for debugging and auditing.

---

## Configuration & Environment

- The `.env` file is stored at `Misc/.env` and holds sensitive credentials and email recipient list in `key=value` format.  
- A GitHub token can optionally be set in `.env` as `GITHUB_TOKEN` to increase API rate limits during update checks.  
- Executable binaries are stored in the `bin` folder relative to the launcher root directory.  
- Logs and Python bytecode caches are stored in dedicated folders under `logs/`.

---

## Requirements

- Python 3.10+ (required for development and packaging).  
- Dependencies are listed in `requirements.txt`, including:  
  - `tkinter`, `tkcalendar`, `tkinterdnd2`  
  - `playwright`  
  - `python-dotenv`  
  - `requests`  
  - `RapidFuzz`  
  - `tqdm`  
  - `pandas`, `numpy`, `openpyxl` (optional dependencies)  
- Primarily tested on Windows environments.

---

## Development & Contribution

- The launcher uses `tkinter` for the UI and `subprocess` for launching child applications.  
- Version information and update checking are handled via GitHub API and release assets.  
- The external updater executable (`Updater.exe`) safely replaces running executables during updates.  
- To test locally:  
  1. Clone the repository.  
  2. Install dependencies with `pip install -r requirements.txt`.  
  3. Run `calendarbuddy.py`.  
- Contributions are welcome, including UI improvements, additional app integrations, and update robustness.  
- Please report issues or submit pull requests via the GitHub repository.

---

## Limitations & Notes

- The update process requires the external `Updater.exe` helper to replace executables safely.  
- Currently tested primarily on Windows.  
- GitHub token usage is optional but recommended to avoid API rate limiting.  
- Known issue: `Updater.exe` may be blocked by some security software (likely false positive). No estimated time for resolution.  
- Code signing the updater executable would resolve security warnings but requires a code signing certificate.

---

## Legal & Disclaimer

This tool is intended for internal use by authorized parties only. No warranties or guarantees are provided. Use responsibly and ensure proper credential handling.

---

## Contact

For support or feature requests, please submit a GitHub Issue in the repository.