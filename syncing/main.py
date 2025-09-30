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
status = "Idle"


def write_env():
    DOTENV.write_text("\n".join(f"{k}={v}" for k, v in CONFIG.items()))


def run_config_window():
    import tkinter as tk
    from tkinter import ttk, filedialog

    conf = load_config()
    host = conf.get("HOST", "")
    api_key = conf.get("API_KEY", "")
    api_secret = conf.get("API_SECRET", "")
    client_id = conf.get("CLIENT_ID", "")
    folder = conf.get("PATH", "")

    root = tk.Tk()
    root.title("Sync Settings")
    root.geometry("500x400")  # Increased height to accommodate descriptions

    # --- bring window to front ---
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)
    root.focus_force()

    # use ttk styles
    style = ttk.Style(root)
    style.configure("TLabel", font=("Segoe UI", 11))
    style.configure("TEntry", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 11))
    style.configure("Description.TLabel", font=("Segoe UI", 9), foreground="gray")

    # main frame with padding
    frame = ttk.Frame(root, padding=15)
    frame.pack(fill="both", expand=True)

    # Site row (now at row 0)
    ttk.Label(frame, text="Site:").grid(row=0, column=0, sticky="w", pady=(5, 0))
    host_entry = ttk.Entry(frame)
    host_entry.insert(0, host)
    host_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(5, 0))
    ttk.Label(frame, text="Your site URL (e.g., https://example.com)", style="Description.TLabel").grid(
        row=1, column=1, columnspan=2, sticky="w", pady=(0, 5)
    )

    # API Key (now at row 2)
    ttk.Label(frame, text="API Key:").grid(row=2, column=0, sticky="w", pady=(5, 0))
    api_key_entry = ttk.Entry(frame)
    api_key_entry.insert(0, api_key)
    api_key_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(5, 0))
    ttk.Label(frame, text="Public API key for authentication. Get from Desk.", style="Description.TLabel").grid(
        row=3, column=1, columnspan=2, sticky="w", pady=(0, 5)
    )

    # API Secret (now at row 4)
    ttk.Label(frame, text="API Secret:").grid(row=4, column=0, sticky="w", pady=(5, 0))
    api_secret_entry = ttk.Entry(frame, show="*")
    api_secret_entry.insert(0, api_secret)
    api_secret_entry.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(5, 0))
    ttk.Label(frame, text="Private API secret (kept secure). Get from Desk.", style="Description.TLabel").grid(
        row=5, column=1, columnspan=2, sticky="w", pady=(0, 5)
    )

    # Client ID (now at row 6)
    ttk.Label(frame, text="Client ID:").grid(row=6, column=0, sticky="w", pady=(5, 0))
    client_id_entry = ttk.Entry(frame)
    client_id_entry.insert(0, client_id)
    client_id_entry.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(5, 0))
    ttk.Label(frame, text="Get your client ID from your site administrator.", style="Description.TLabel").grid(
        row=7, column=1, columnspan=2, sticky="w", pady=(0, 5)
    )

    # Folder row (now at row 8)
    ttk.Label(frame, text="Drive Folder:").grid(row=8, column=0, sticky="w", pady=(5, 0))
    folder_var = tk.StringVar(value=folder)
    folder_entry = ttk.Entry(frame, textvariable=folder_var)
    folder_entry.grid(row=8, column=1, sticky="ew", pady=(5, 0))

    def choose_folder():
        new = filedialog.askdirectory()
        if new:
            folder_var.set(new)

    browse_btn = ttk.Button(frame, text="Browse", command=choose_folder)
    browse_btn.grid(row=8, column=2, padx=5, pady=(5, 0))

    ttk.Label(frame, text="Local folder to sync your Drive with.", style="Description.TLabel").grid(
        row=9, column=1, columnspan=2, sticky="w", pady=(0, 5)
    )

    style.configure("Save.TButton", padding=10)

    def save_and_close():
        CONFIG["HOST"] = host_entry.get()
        CONFIG["API_KEY"] = api_key_entry.get()
        CONFIG["API_SECRET"] = api_secret_entry.get()
        CONFIG["CLIENT_ID"] = client_id_entry.get()
        CONFIG["PATH"] = folder_var.get()
        write_env()
        root.destroy()

    # Save button (now at row 10)
    save_btn = ttk.Button(frame, text="Save", command=save_and_close, style="Save.TButton")
    save_btn.grid(row=10, column=0, columnspan=3, pady=(20, 10), sticky="ew")

    # make columns stretch properly
    frame.columnconfigure(1, weight=1)

    root.mainloop()


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
    if len(CONFIG):
        t = threading.Thread(target=sync_worker, daemon=True)
        t.start()
    else:
        open_settings_process()

    icon.run()  # this blocks until icon.stop() is called


def get_status_text(text):
    return f"Status: {status}" if CONFIG else "Not yet synced - setup Drive"


def on_quit(icon, item):
    global running
    running = False
    icon.stop()
    if observer:
        observer.stop()


def on_open_settings(icon, item):
    open_settings_process()


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
observer = None


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


# --- entry point ------------------------------------------------------------
if __name__ == "__main__":
    if CONFIG:
        from utils import sync_folder, PersistentMap, get, listen_to_updates
        from watcher import Watcher

        STORAGE = PersistentMap(Path("./sync_log.json"))
        PATH = CONFIG.get("PATH")
    if "--config-window" in sys.argv:
        run_config_window()
        sys.exit(0)
    else:
        main_tray()
