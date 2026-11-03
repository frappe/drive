from drive.utils.files import FileManager
from drive.utils.maintenance import inspect_paths


def execute():
    """Repair only verified paths within the same team's private storage."""
    manager = FileManager()
    if manager.flat or manager.s3_enabled:
        return
    return inspect_paths(apply=True)
