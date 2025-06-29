import sys
import os
import subprocess
import threading
import datetime
import requests
import shutil
import tempfile
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv, set_key

__version__ = '0.1.1'  # Update this version as needed - 'major.minor.patch'
GITHUB_OWNER = 'DaSonOfPoseidon'
GITHUB_REPO = 'CalendarBuddy'

def get_latest_release_info(app_name):
    """
    Fetch latest GitHub release data and return (tag_name, download_url) for matching asset.
    This version fetches from the 'exeFiles' repo where your built .exes are stored.
    """
    EXE_REPO_OWNER = "DaSonOfPoseidon"
    EXE_REPO_NAME = "exeFiles"
    url = f"https://api.github.com/repos/{EXE_REPO_OWNER}/{EXE_REPO_NAME}/releases/latest"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tag_name = data.get('tag_name')
        assets = data.get('assets', [])
        for asset in assets:
            name = asset.get('name', '')
            if name.lower() == app_name.lower():
                return tag_name, asset.get('browser_download_url')
        print(f"[Update] No asset named '{app_name}' found in exeFiles latest release")
    except Exception as e:
        print(f"[Update] Error fetching latest release info from exeFiles repo: {e}")
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

def maybe_update(app_name, current_version, is_launcher=False):
    latest_version, download_url = get_latest_release_info(app_name)
    if not latest_version or not download_url:
        print(f"[Update] Could not find latest release info for {app_name}")
        return

    def norm_ver(v): return v.lstrip('vV')

    if norm_ver(latest_version) <= norm_ver(current_version):
        print(f"[No Update] {app_name} is up to date ({current_version})")
        return

    print(f"[Update] {app_name} update available: {current_version} → {latest_version}")

    app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    bin_folder = os.path.join(app_dir, "bin")
    os.makedirs(bin_folder, exist_ok=True)

    if is_launcher:
        old_exe_path = os.path.join(app_dir, f"{app_name}.exe")
        new_exe_path = os.path.join(app_dir, f"{app_name}_update.exe")
        updater_path = os.path.join(bin_folder, "Updater.exe")
    else:
        old_exe_path = os.path.join(bin_folder, f"{app_name}.exe")
        new_exe_path = os.path.join(bin_folder, f"{app_name}_update.exe")
        updater_path = os.path.join(bin_folder, "Updater.exe")

    if download_update(download_url, new_exe_path):
        print(f"[Update] Downloaded new version to {new_exe_path}")
        if not os.path.exists(updater_path):
            print(f"[Update] Updater.exe not found in {bin_folder}, cannot update now.")
            return
        try:
            print(f"[Update] Launching Updater.exe to replace {old_exe_path}")
            subprocess.run([updater_path, old_exe_path, new_exe_path], check=True)

            print(f"[Update] Replacement complete for {app_name}")

            if is_launcher:
                print("[Update] Restarting launcher")
                subprocess.Popen([old_exe_path])
                sys.exit(0)
        except Exception as e:
            print(f"[Update] Error running Updater.exe: {e}")
    else:
        print("[Update] Failed to download update")
# ────────────────────────────────────────────────────────────────────────────────

# ─── APPLICATION DIRECTORY ─────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, '_MEIPASS', APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

ENV_PATH    = os.path.join(APP_DIR, '.env')
INTERPRETER = os.path.join(RESOURCE_DIR, 'embedded_python', 'python.exe') #unneeded, but kept for backwards compatibility
if not os.path.isfile(INTERPRETER):
    INTERPRETER = sys.executable

BRANCH = 'main'


LOGS_DIR    = os.path.join(APP_DIR, 'logs')
PYCACHE_DIR = os.path.join(LOGS_DIR, 'pycache')
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


def run_job(label):
    # Determine the child EXE name and path
    # Suppose you have a map from label to exe-base-name:
    APP_NAME_MAP = {
        'Run Assigner': 'ASSigner',
        'Run Scraper': 'JobScraper',
        'Run Spreader': 'ButterKnife',
        'Run Tasks': 'ConsultationCrusher',
    }
    exe_base = APP_NAME_MAP.get(label)
    if not exe_base:
        print(f"[Error] Unknown label: {label}")
        return

    # Build the path to the child EXE
    app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    exe_name = f"{exe_base}.exe"
    exe_path = os.path.join(app_dir, "bin" , exe_name)

    # 1) Get current version by calling the EXE with --version
    current_version = get_child_version(exe_path)
    if current_version is None:
        print(f"[Update] Could not determine version for {exe_name}, skipping update check.")
    else:
        # 2) Check for update
        maybe_update(exe_base, current_version)

    # 3) Launch the child EXE as subprocess
    if os.path.isfile(exe_path):
        try:
            # Launch without waiting; detach from launcher if desired
            subprocess.Popen([exe_path], cwd=app_dir)
        except Exception as e:
            print(f"[Launch] Failed to run {exe_name}: {e}")
    else:
        print(f"[Launch] Executable not found: {exe_path}")

def get_child_version(exe_path, timeout=5):
    """
    Run `exe_path --version` and return the version string.
    If it fails, return 0.0.0.
    """
    if not os.path.isfile(exe_path):
        print(f"[Version] Executable not found: {exe_path}")
        return None
    try:
        # Use a small timeout so it doesn't hang
        # On Windows, subprocess.run with list args is fine:
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
    # Self-update the launcher itself
    maybe_update('CalendarBuddy', __version__, True)
    root = tk.Tk()
    App(root)
    root.mainloop()
