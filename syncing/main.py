# sync_app.py
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

from pystray import Icon, Menu, MenuItem
from PIL import Image
from dotenv import dotenv_values

from watchdog.observers import Observer

ICON_PATH = Path("icon.png")
DOTENV = Path(".env")


def load_config():
    if DOTENV.exists():
        return dotenv_values(DOTENV)
    return {}


CONFIG = load_config()


def write_env():
    DOTENV.write_text("\n".join(f"{k}={v}" for k, v in CONFIG.items()))


def run_config_window():
    # This function will run in its own process and contains its own Tk mainloop.
    import tkinter as tk
    from tkinter import filedialog

    conf = load_config()
    api_key = conf.get("API_KEY", "")
    api_secret = conf.get("API_SECRET", "")
    folder = conf.get("PATH", "")

    root = tk.Tk()
    root.title("Sync Settings")
    root.geometry("480x220")

    tk.Label(root, text="API Key:").pack(anchor="w", padx=10, pady=(8, 0))
    api_key_entry = tk.Entry(root, width=60)
    api_key_entry.insert(0, api_key)
    api_key_entry.pack(padx=10)

    tk.Label(root, text="API Secret:").pack(anchor="w", padx=10, pady=(8, 0))
    api_secret_entry = tk.Entry(root, width=60, show="*")
    api_secret_entry.insert(0, api_secret)
    api_secret_entry.pack(padx=10)

    tk.Label(root, text="Folder to sync:").pack(anchor="w", padx=10, pady=(8, 0))
    folder_var = tk.StringVar(value=folder)
    folder_entry = tk.Entry(root, textvariable=folder_var, width=50)
    folder_entry.pack(side="left", padx=(10, 0), pady=4)

    def choose_folder():
        new = filedialog.askdirectory()
        if new:
            folder_var.set(new)

    tk.Button(root, text="Browse", command=choose_folder).pack(side="left", padx=8)

    def save_and_close():
        CONFIG["API_KEY"] = api_key_entry.get()
        CONFIG["API_SECRET"] = api_secret_entry.get()
        CONFIG["PATH"] = folder_var.get()
        write_env()
        root.destroy()

    tk.Button(root, text="Save", command=save_and_close).pack(pady=12)

    root.mainloop()


if CONFIG:
    from utils import sync_folder, PersistentMap, get, listen_to_updates
    from watcher import Watcher
else:
    run_config_window()


def open_settings_process():
    """
    Launch a separate process that runs the same executable/script with
    --config-window. This pattern works well when you later bundle with PyInstaller.
    """
    if getattr(sys, "frozen", False):
        args = [sys.executable, "--config-window"]
    else:
        script = os.path.abspath(sys.argv[0])
        args = [sys.executable, script, "--config-window"]

    # Don't block the tray. Let the user close the settings window independently.
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


running = True
status = "Idle"
observer = None

STORAGE = PersistentMap(Path("./sync_log.json"))
PATH = CONFIG.get("PATH")


def sync_worker():
    global status, running, observer
    HOME_TEAM = get("utils.get_default_team")
    HOME_ENTITY = get("api.files.get_root_folder", team=HOME_TEAM)
    try:
        if not CONFIG:
            print("Authenticate first!")
            status = "Setup Drive"
        else:
            if not len(STORAGE):
                sync_folder(HOME_ENTITY["name"], HOME_ENTITY["path"], STORAGE)
            event_handler = Watcher(STORAGE, PATH, HOME_TEAM)
            observer = Observer()
            observer.schedule(event_handler, PATH, recursive=True)
            observer.start()
            print("Listening for file changes:")
            listen_to_updates(STORAGE, HOME_ENTITY["path"])
            while running:
                status = "Syncing"
    except BaseException as e:
        print(e)
        # log error, set status appropriately
        status = "Error"
        time.sleep(2)
    finally:
        if observer:
            observer.stop()


def get_status_text(text):
    return f"Status: {status}"


def on_quit(icon, item):
    global running
    running = False
    icon.stop()
    if observer:
        observer.stop()


def on_open_settings(icon, item):
    open_settings_process()


def main_tray():
    # load icon image (ensure the path exists or use a default)
    if ICON_PATH.exists():
        img = Image.open(str(ICON_PATH))
    else:
        # create a fallback tiny image
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

    menu = Menu(
        MenuItem(get_status_text, None, enabled=False),
        Menu.SEPARATOR,
        MenuItem("Settings", on_open_settings),
        MenuItem("Quit", on_quit),
    )

    icon = Icon("SyncApp", img, menu=menu)

    # start sync worker in background thread
    t = threading.Thread(target=sync_worker, daemon=True)
    t.start()

    icon.run()  # this blocks until icon.stop() is called


# --- entry point ------------------------------------------------------------
if __name__ == "__main__":
    if "--config-window" in sys.argv:
        run_config_window()
        sys.exit(0)
    else:
        main_tray()
