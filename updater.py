# Updater.py

import sys
import time
import os
import shutil
import subprocess

def wait_for_file_unlock(file_path, timeout=30, interval=0.5):
    """Wait until the file is unlocked (not opened by any process)."""
    start_time = time.time()
    while True:
        try:
            # Try opening the file in append mode to test if it's locked.
            with open(file_path, "a"):
                return True
        except (OSError, IOError):
            if time.time() - start_time > timeout:
                return False
            time.sleep(interval)

def main():
    if len(sys.argv) < 3:
        print("Usage: Updater.exe <old_exe_path> <new_exe_path>")
        sys.exit(1)

    old_exe = sys.argv[1]
    new_exe = sys.argv[2]

    print(f"Updater started.\nOld exe: {old_exe}\nNew exe: {new_exe}")

    if not os.path.exists(new_exe):
        print(f"New executable not found: {new_exe}")
        sys.exit(2)

    # Wait for old exe to unlock (i.e. main app exited)
    print("Waiting for old executable to be unlocked...")
    if not wait_for_file_unlock(old_exe):
        print("Timeout waiting for old executable to be unlocked.")
        sys.exit(3)

    try:
        # Optionally back up the old exe before replacement (safe fallback)
        backup_path = old_exe + ".bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(old_exe, backup_path)
        print(f"Backed up old executable to {backup_path}")
    except Exception as e:
        print(f"Warning: Could not back up old executable: {e}")

    try:
        # Replace old exe with new exe (move new exe into old exe location)
        os.replace(new_exe, old_exe)
        print("Replacement successful.")
    except Exception as e:
        print(f"Failed to replace executable: {e}")
        # Attempt to restore from backup if available
        if os.path.exists(backup_path):
            os.rename(backup_path, old_exe)
            print("Restored old executable from backup.")
        sys.exit(4)

    # Clean up backup if replacement succeeded
    if os.path.exists(backup_path):
        os.remove(backup_path)

    try:
        # Restart the main app detached
        print("Restarting main app...")
        subprocess.Popen([old_exe], close_fds=True)
        print("Main app restarted successfully.")
    except Exception as e:
        print(f"Failed to restart main app: {e}")
        sys.exit(5)

    print("Updater finished successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
