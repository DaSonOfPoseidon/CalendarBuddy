import sys
import os
import subprocess
import threading
import datetime
import json
import requests
import shutil
import tempfile
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv, set_key

__version__ = '0.1.6'  # Update this version as needed - 'major.minor.patch'
GITHUB_OWNER = 'DaSonOfPoseidon'
GITHUB_REPO = 'CalendarBuddy'

APPS = {
    'ASSigner': {
        'label': 'Run Assigner',
        'repo': ('DaSonOfPoseidon', 'JobAssignment'),
    },
    'JobScraper': {
        'label': 'Run Scraper',
        'repo': ('DaSonOfPoseidon', 'JobScraper'),
    },
    'ButterKnife': {
        'label': 'Run Spreader',
        'repo': ('DaSonOfPoseidon', 'JobScraper'),
    },
    'ConsultationCrusher': {
        'label': 'Run Tasks',
        'repo': ('DaSonOfPoseidon', 'TaskScraper'),
    },
    'Updater': {
        'repo': ('DaSonOfPoseidon', 'CalendarBuddy'),
    },
}

def get_latest_release_info(app_name: str):
    """
    Given an app_name (e.g. 'ASSigner' or 'CalendarBuddy'),
    look up its GitHub repo in APPS (or use the launcher repo if missing),
    then fetch /releases/latest and return (tag, download_url) for the first
    .exe whose base name starts with app_name.
    """
    # pick the right repo tuple
    owner, repo = APPS.get(app_name, {}).get('repo', (GITHUB_OWNER, GITHUB_REPO))

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    tag_name = data.get("tag_name")

    for asset in data.get("assets", []):
        name = asset.get("name", "")
        base, ext = os.path.splitext(name)
        if ext.lower() == ".exe" and base.lower().startswith(app_name.lower()):
            return tag_name, asset["browser_download_url"]

    return None, None

def download_update(url, dest_path):
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return True
    except Exception as e:
        print(f"[Update] Failed to download update: {e}")
        return False

def ensure_updater_installed(bin_dir):
    updater_path = os.path.join(bin_dir, "Updater.exe")
    if not os.path.isfile(updater_path):
        tag, url = get_latest_release_info("Updater")
        if tag and url:
            os.makedirs(bin_dir, exist_ok=True)
            if download_update(url, updater_path):
                print(f"[Setup] Updater.exe v{tag} installed")
            else:
                print("[Setup] Failed to download Updater.exe")
        else:
            print("[Setup] No Updater.exe asset found")

def maybe_update(app_name, current_version, is_launcher=False) -> bool:
    """
    Returns True if an update was performed (and Updater.exe was run),
    False otherwise.
    """
    latest_version, download_url = get_latest_release_info(app_name)
    if not latest_version or not download_url:
        print(f"[Update] Could not find latest release info for {app_name}")
        return False

    def norm_ver(v): return v.lstrip('vV')
    if norm_ver(latest_version) <= norm_ver(current_version):
        print(f"[No Update] {app_name} is up to date ({current_version})")
        return False

    print(f"[Update] {app_name} update available: {current_version} → {latest_version}")

    app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    bin_folder = os.path.join(app_dir, "bin")
    os.makedirs(bin_folder, exist_ok=True)

    # paths for old/new exe
    if is_launcher:
        old_exe = os.path.join(app_dir, f"{app_name}.exe")
        new_exe = os.path.join(app_dir, f"{app_name}_update.exe")
    else:
        old_exe = os.path.join(bin_folder, f"{app_name}.exe")
        new_exe = os.path.join(bin_folder, f"{app_name}_update.exe")

    updater = os.path.join(bin_folder, "Updater.exe")

    # download the update
    if not download_update(download_url, new_exe):
        print("[Update] Failed to download update")
        return False

    print(f"[Update] Downloaded new version to {new_exe}")
    if not os.path.exists(updater):
        print(f"[Update] Updater.exe not found in {bin_folder}, cannot update now.")
        return False

    if is_launcher:
        # launcher: fire-and-exit so the file lock is released
        print(f"[Update] Launching Updater.exe to replace {old_exe}")
        subprocess.Popen([updater, old_exe, new_exe], cwd=bin_folder)
        print("[Update] Exiting launcher to allow update")
        sys.exit(0)
    else:
        # child: run updater synchronously and then return True
        try:
            print(f"[Update] Launching Updater.exe to replace {old_exe}")
            subprocess.run([updater, old_exe, new_exe], cwd=bin_folder, check=True)
            print(f"[Update] Replacement complete for {app_name}")
            return True
        except Exception as e:
            print(f"[Update] Error running Updater.exe: {e}")
            return False
# ────────────────────────────────────────────────────────────────────────────────

# ─── APPLICATION DIRECTORY ─────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, '_MEIPASS', APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR
MISC_DIR     = os.path.join(APP_DIR, "Misc")
BIN_DIR = os.path.join(APP_DIR, "bin")
ENV_PATH    = os.path.join(MISC_DIR, '.env')
INTERPRETER = os.path.join(RESOURCE_DIR, 'embedded_python', 'python.exe') #unneeded, but kept for backwards compatibility
if not os.path.isfile(INTERPRETER):
    INTERPRETER = sys.executable

BRANCH = 'main'


LOGS_DIR    = os.path.join(APP_DIR, 'logs')
PYCACHE_DIR = os.path.join(LOGS_DIR, 'pycache')

os.makedirs(MISC_DIR, exist_ok=True)
VERSION_FILE = os.path.join(MISC_DIR, "versions.json")
os.makedirs(PYCACHE_DIR, exist_ok=True)
os.environ['PYTHONPYCACHEPREFIX'] = PYCACHE_DIR
os.makedirs(LOGS_DIR, exist_ok=True)
# ────────────────────────────────────────────────────────────────────────────────

if not os.path.exists(ENV_PATH):
    open(ENV_PATH, 'w').close()
load_dotenv(ENV_PATH)

class App:
    def __init__(self, root):
        self.root = root
        root.title(f'CalendarBuddy Launcher v{__version__}')
        self.buttons = {}

        # Settings frame
        settings = tk.LabelFrame(root, text='Settings')
        settings.pack(fill='x', padx=10, pady=5)

        tk.Label(settings, text='UNITY_USER').grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.unity_user = tk.Entry(settings, width=40)
        self.unity_user.insert(0, os.getenv('UNITY_USER', ''))
        self.unity_user.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(settings, text='PASSWORD').grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.password = tk.Entry(settings, width=40, show='*')
        self.password.insert(0, os.getenv('PASSWORD', ''))
        self.password.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(settings, text='EMAIL_RECIPIENTS').grid(row=2, column=0, sticky='ne', padx=5, pady=2)
        self.recipients_text = tk.Text(settings, width=38, height=4)
        for i, r in enumerate(os.getenv('EMAIL_RECIPIENTS', '').split(',')):
            r = r.strip()
            if r:
                self.recipients_text.insert(f'{i+1}.0', r + '\n')
        self.recipients_text.grid(row=2, column=1, padx=5, pady=2)

        save_btn = tk.Button(settings, text='Save Settings', command=self.save_settings)
        save_btn.grid(row=3, column=0, columnspan=2, pady=5)

        tk.Label(root, text='Select a program to run:').pack(pady=(10, 0))

        labels = [
            "Run Assigner",
            "Run Scraper",
            "Run Spreader",
            "Run Tasks"
        ]

        for label in labels:
            btn = tk.Button(root, text=label, width=25,
                            command=lambda l=label: self.start_task(l))
            btn.pack(pady=5)
            self.buttons[label] = btn

        self.status = tk.StringVar(value='Ready')
        tk.Label(root, textvariable=self.status, anchor='w').pack(fill='x', padx=10, pady=(5,10))
        root.geometry('360x420')

    def save_settings(self):
        set_key(ENV_PATH, 'UNITY_USER', self.unity_user.get().strip())
        set_key(ENV_PATH, 'PASSWORD', self.password.get().strip())
        recips = [l.strip() for l in self.recipients_text.get('1.0', 'end').splitlines() if l.strip()]
        set_key(ENV_PATH, 'EMAIL_RECIPIENTS', ','.join(recips))
        messagebox.showinfo('Settings Saved', 'Settings have been saved to .env.')

    def set_buttons_state(self, enabled):
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def start_task(self, label):
        self.set_buttons_state(False)
        self.status.set(f"Running '{label}'…")
        threading.Thread(target=self.worker, args=(label,), daemon=True).start()

    def worker(self, label):
        try:
            result = run_job(label)
            self.write_log(label, result)
            self.root.after(0, lambda msg=result: self.finish(True, msg))
        except Exception as exc:
            self.write_log(label, str(exc))
            self.root.after(0, lambda msg=str(exc): self.finish(False, msg))

    def finish(self, success, message):
        self.set_buttons_state(True)
        self.status.set('Ready')
        (messagebox.showinfo if success else messagebox.showerror)('Result', message)

    def write_log(self, label, message):
        safe_label = label.replace(" ", "_").lower()
        log_file = os.path.join(LOGS_DIR, f"{safe_label}.log")
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {label}\n{message}\n\n")

def load_versions():
    """Load the per-app version cache from Misc/versions.json."""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_versions(versions):
    """Save the per-app version cache to Misc/versions.json."""
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(versions, f, indent=2)
    except Exception as e:
        print(f"[Cache] Failed to write {VERSION_FILE}: {e}")

def run_job(label) -> str:
    # 1) Map button label → app_name
    for app_name, meta in APPS.items():
        if meta.get("label") == label:
            break
    else:
        return f"[Error] Unknown label: {label}"

    # 2) Build paths
    app_dir = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(__file__)
    )
    bin_dir = os.path.join(app_dir, "bin")
    exe_name = f"{app_name}.exe"
    exe_path = os.path.join(bin_dir, exe_name)

    # 3) Load version cache
    versions = load_versions()

    # 4) Download if missing (and cache the tag)
    downloaded_tag = None
    if not os.path.isfile(exe_path):
        tag, url = get_latest_release_info(app_name)
        if tag and url:
            os.makedirs(bin_dir, exist_ok=True)
            if download_update(url, exe_path):
                print(f"[Download] {exe_name} v{tag} → {exe_path}")
                downloaded_tag = tag
                versions[app_name] = tag
                save_versions(versions)
            else:
                return f"[Download] Failed to download {exe_name}"
        else:
            return f"[Download] No {exe_name} asset found for {app_name}"

    # 5) Determine current_version
    if downloaded_tag:
        current_version = downloaded_tag
    else:
        current_version = versions.get(app_name)
        if current_version is None:
            current_version = get_child_version(exe_path)

    # 6) Self-update; maybe_update now returns True if it replaced & relaunched
    update_happened = False
    if current_version:
        update_happened = maybe_update(app_name, current_version)
        if update_happened:
            # refresh cache if GitHub tag changed
            latest_tag, _ = get_latest_release_info(app_name)
            if latest_tag and latest_tag != current_version:
                versions[app_name] = latest_tag
                save_versions(versions)
            return f"[Update] {exe_name} replaced and launched"
    else:
        print(f"[Update] Could not determine version for {exe_name}, skipping update.")

    # 7) Normal launch (only if no update was performed)
    try:
        subprocess.Popen([exe_path], cwd=app_dir)
        return f"[Launch] {exe_name} started"
    except Exception as e:
        return f"[Launch] Failed to run {exe_name}: {e}"

def get_child_version(exe_path, timeout=30):
    """
    Run `exe_path --version` and return the version string.
    If it fails or exe is missing, return None.
    """
    if not os.path.isfile(exe_path):
        print(f"[Version] Executable not found: {exe_path}")
        return None
    try:
        result = subprocess.run(
            [exe_path, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            version = result.stdout.strip().splitlines()[0].strip()
            print(f"[Version] {os.path.basename(exe_path)} version: {version}")
            return version
        else:
            print(f"[Version] Non-zero exit from {exe_path} --version: {result.returncode}")
            return None
    except Exception as e:
        print(f"[Version] Error getting version from {exe_path}: {e}")
        return None


if __name__ == '__main__':
    ensure_updater_installed(BIN_DIR)
    maybe_update('CalendarBuddy', __version__, True)
    root = tk.Tk()
    App(root)
    root.mainloop()
