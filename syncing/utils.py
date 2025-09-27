import requests
from dotenv import dotenv_values
from pathlib import Path
import threading
import json


CONFIG = dotenv_values()
PATH = Path(CONFIG["PATH"])
session = requests.Session()
session.auth = (CONFIG["API_KEY"], CONFIG["API_SECRET"])

url_prefix = lambda path: CONFIG["HOST"] + "/api/method/drive." + path


class PersistentMap(dict):
    def __init__(self, path: Path):
        self.path = path
        if self.path.exists():
            try:
                with open(self.path) as f:
                    super().update(json.load(f))
            except json.JSONDecodeError:
                pass

    def sync(self):
        with open(self.path, "w") as f:
            json.dump(self, f, indent=2)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.sync()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.sync()

    def reverse_lookup(self, search):
        for key, val in self.items():
            if val == search:
                return key
        raise KeyError("Could not find: ", search)


def get(path, **params):
    r = session.get(url_prefix(path), params=params)
    if r.status_code != 200:
        raise ValueError(r.json())
    return r.json()["message"]


from contextlib import contextmanager

_local_changes = set()
_lock = threading.Lock()


def suppress_watchdog(path: Path):
    p = path.resolve()
    with _lock:
        _local_changes.add(p)


def is_local_change(path: Path) -> bool:
    p = path.resolve()
    with _lock:
        if p in _local_changes:
            _local_changes.remove(p)
            return True
    return False


def sync_folder(entity_name, team_folder, storage):
    files = get("api.list.files?entity_name=" + entity_name)
    folder_details = get("api.permissions.get_entity_with_permissions?entity_name=" + entity_name)

    folder_path = Path(folder_details["path"]).relative_to(team_folder)
    (PATH / folder_path).mkdir(exist_ok=True)
    storage[str(folder_path)] = entity_name

    for k in files:
        try:
            new_path = Path(k["path"]).relative_to(team_folder)
        except:
            print("Issue with:", k)
            continue
        if k["is_group"]:
            sync_folder(k["name"], team_folder, storage)
        else:
            with open(PATH / new_path, "wb") as f:
                file_data = session.get(url_prefix("api.files.get_file_content?entity_name=" + k["name"]))
                if file_data.status_code != 200:
                    print("There was an issue with:", k["name"])
                else:
                    f.write(file_data.content)
                    storage[str(new_path)] = k["name"]


def listen_to_updates(storage):
    threading.Timer(5.0, listen_to_updates, kwargs={"storage": storage}).start()
    updates = get("api.product.get_updates", client=CONFIG["CLIENT_ID"])
    print("Polled server for updates, getting", len(updates))

    for update in updates:
        current_path = storage.reverse_lookup(update["entity"])
        disk_path = PATH / current_path
        if update["type"] in ["move", "rename"]:
            suppress_watchdog(disk_path)
            new_path = PATH / update["details"]
            disk_path.rename(new_path)
            storage[str(new_path.relative_to(PATH))] = storage.pop(current_path)
            session.post(url_prefix("api.product.pop_update"), {"name": update["name"]})
