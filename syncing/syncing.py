from pathlib import Path

from watchdog.observers import Observer
from dotenv import dotenv_values

from utils import sync_folder, PersistentMap, get
from watcher import Watcher


HOME_TEAM = get("utils.get_default_team")
HOME_ENTITY = get("api.files.get_root_folder", team=HOME_TEAM)

STORAGE = PersistentMap(Path("./sync_log.json"))
PATH = dotenv_values()["PATH"]
sync_folder(HOME_ENTITY["name"], HOME_ENTITY["path"], STORAGE)


try:
    event_handler = Watcher(STORAGE, PATH, HOME_TEAM)
    observer = Observer()
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()
    print("Listening for file changes:")

    import time

    while True:
        time.sleep(1)
finally:
    observer.stop()
    observer.join()
