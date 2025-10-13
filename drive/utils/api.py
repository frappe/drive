from drive.api.permissions import get_user_access
from drive.utils import get_file_type


def get_default_access(entity_name):
    default = 0
    if entity_name:
        if get_user_access(entity_name, "Guest")["read"]:
            default = -2
        elif get_user_access(entity_name, team=1)["read"]:
            default = -1
    return default


def prettify_file(f: dict):
    f["file_type"] = get_file_type(f)
    f["share_count"] = get_default_access(f)
    return f
