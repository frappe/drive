import json
from pathlib import Path

import requests
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

url_prefix = lambda x: "http://127.0.0.1:8081/api/method/drive.api." + x
PATH = Path("/Users/sfwn/FDrive")
MAP = {}


class WatchChanges(FileSystemEventHandler):
    def on_modified(self, event: FileModifiedEvent) -> None:
        if event.is_directory:
            return
        drive_path = Path(event.src_path).relative_to(PATH)
        drive_name = MAP.get(str(drive_path))
        if not drive_name:
            return
        with open(event.src_path, "rb") as f:
            r = requests.post(url_prefix(f"files.edit_file_content?entity_name={drive_name}"), files={"file": f})
            print(r)

    def on_created(self, event):
        drive_path = Path(event.src_path).relative_to(PATH)
        if str(drive_path) in MAP:
            # Editing, not creating
            return self.on_modified(event)
        with open(event.src_path, "rb") as f:
            r = requests.post(
                url_prefix("files.upload_file"),
                params={"team": "jnssefk6d8", "parent": MAP[str(drive_path.parent)]},
                files={"file": f},
            )
            MAP[str(drive_path)] = r.json()["message"]["name"]
        print(MAP)
        with open("./sync_log.json", "w") as f:
            json.dump(MAP, f)

    # def on_moved(self, event) -> None:
    #     drive_path = Path(event.src_path).relative_to(PATH)
    #     entity = MAP[str(drive_path)]
    #     dest_path = Path(event.dest_path).relative_to(PATH)
    #     dest_entity = dest_path.parent
    #     r = requests.post(url_prefix("files.move"), params={"entities": [entity], "new_parent": MAP[str(dest_entity)]})
    #     MAP[str(dest_path)] = MAP.pop(str(drive_path))
    #     with open("./sync_log.json", "w") as f:
    #         json.dump(MAP, f)


def sync_folder(entity_name):
    file_list_request = requests.get(url_prefix("list.files?entity_name=" + entity_name))
    files = file_list_request.json()["message"]
    entity_request = requests.get(url_prefix("permissions.get_entity_with_permissions?entity_name=" + entity_name))
    folder_details = entity_request.json()["message"]
    team_folder = Path(folder_details["path"]).parts[0]
    folder_path = Path(folder_details["path"]).relative_to(team_folder)
    (PATH / folder_path).mkdir(exist_ok=True)
    MAP[str(folder_path)] = entity_name
    for k in files:
        new_path = Path(k["path"]).relative_to(team_folder)
        if k["is_group"]:
            sync_folder(k["name"])
        else:
            with open(PATH / new_path, "wb") as f:
                file_data = requests.get(url_prefix("files.get_file_content?entity_name=" + k["name"]))
                f.write(file_data.content)
                MAP[str(new_path)] = k["name"]

    with open("./sync_log.json", "w") as f:
        json.dump(MAP, f)


try:
    with open("./sync_log.json") as f:
        MAP = json.load(f)
except FileNotFoundError:
    pass

# sync_folder("jq0nhbbdp2")
try:
    event_handler = WatchChanges()
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
