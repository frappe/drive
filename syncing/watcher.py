from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from pathlib import Path
import json
from dotenv import dotenv_values
import requests
from utils import url_prefix

CONFIG = dotenv_values()

import threading


def debounce(wait_time):
    """
    Decorator that will debounce a function so that it is called after wait_time seconds
    If it is called multiple times, will wait for the last call to be debounced and run only this one.
    """

    def decorator(function):
        def debounced(*args, **kwargs):
            def call_function():
                debounced._timer = None
                return function(*args, **kwargs)

            # if we already have a call to the function currently waiting to be executed, reset the timer
            if debounced._timer is not None:
                debounced._timer.cancel()

            # after wait_time, call the function provided to the decorator with its arguments
            debounced._timer = threading.Timer(wait_time, call_function)
            debounced._timer.start()

        debounced._timer = None
        return debounced

    return decorator


class Watcher(FileSystemEventHandler):
    def __init__(self, storage, root_path, team):
        self.storage = storage
        self.root_path = root_path
        self.team = team
        self.sesh = requests.Session()
        self.sesh.auth = (CONFIG["API_KEY"], CONFIG["API_SECRET"])

    @debounce(1)
    def on_modified(self, event: FileModifiedEvent) -> None:
        if event.is_directory:
            return
        drive_path = Path(event.src_path).relative_to(self.root_path)
        drive_name = self.storage.get(str(drive_path))
        if not drive_name:
            return
        with open(event.src_path, "rb") as f:
            self.sesh.post(url_prefix(f"api.files.edit_file_content?entity_name={drive_name}"), files={"file": f})
        print("Edited file:", drive_path)

    @debounce(1)
    def on_created(self, event):
        drive_path = Path(event.src_path).relative_to(self.root_path)
        if str(drive_path) in self.storage:
            # Editing, not creating
            return self.on_modified(event)
        with open(event.src_path, "rb") as f:
            r = self.sesh.post(
                url_prefix("api.files.upload_file"),
                params={"team": self.team, "parent": self.storage[str(drive_path.parent)]},
                files={"file": f},
            )
            self.storage[str(drive_path)] = r.json()["message"]["name"]
        print("Uploaded file:", drive_path)

    @debounce(1)
    def on_moved(self, event) -> None:
        drive_path = Path(event.src_path).relative_to(self.root_path)
        entity = self.storage[str(drive_path)]
        dest_path = Path(event.dest_path).relative_to(self.root_path)
        dest_entity = dest_path.parent
        is_rename = drive_path.parent == dest_entity
        if is_rename:
            r = self.sesh.post(
                url_prefix("api.files.call_controller_method"),
                params={"method": "rename", "entity_name": entity, "new_title": dest_path.parts[-1]},
            )
        else:
            r = self.sesh.post(
                url_prefix("api.files.move"),
                params={"entity_names": json.dumps([entity]), "new_parent": self.storage[str(dest_entity)]},
            )
        if r.status_code != 200:
            print(f"There was an error while moving {drive_path}!")
        else:
            self.storage[str(dest_path)] = self.storage.pop(str(drive_path))
            print(f"Moved file from {drive_path} to {dest_path}")

    def on_deleted(self, event):
        print("Deleted!", event)


# Issue at hand - editing (at disk) is often deleting and recreating. how do we capture that? how do we "delay" deletion to ensure it's not really an edit?
# How do we ignore swap files?
# Are their smarter ways (in Drive) to edit/rename a file instead of creating and deleting (especially at S3 level?)
