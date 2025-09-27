from pathlib import Path

from watchdog.observers import Observer
from dotenv import dotenv_values

from utils import sync_folder, PersistentMap, get, listen_to_updates
from watcher import Watcher

CONFIG = dotenv_values()

HOME_TEAM = get("utils.get_default_team")
HOME_ENTITY = get("api.files.get_root_folder", team=HOME_TEAM)
STORAGE = PersistentMap(Path("./sync_log.json"))
PATH = CONFIG["PATH"]
if not len(STORAGE):
    sync_folder(HOME_ENTITY["name"], HOME_ENTITY["path"], STORAGE)

try:
    event_handler = Watcher(STORAGE, PATH, HOME_TEAM)
    observer = Observer()
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()
    print("Listening for file changes:")
    listen_to_updates(STORAGE)

    import time

    while True:
        time.sleep(1)
finally:
    observer.stop()
    observer.join()
