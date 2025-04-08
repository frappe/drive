import frappe
import os
from pathlib import Path
import hashlib
from PIL import Image, ImageOps
from drive.locks.distributed_lock import DistributedLock
import cv2

DriveFile = frappe.qb.DocType("Drive File")

MIME_LIST_MAP = {
    "Image": [
        "image/png",
        "image/jpeg",
        "image/svg+xml",
        "image/heic",
        "image/heif",
        "image/avif",
        "image/webp",
        "image/tiff",
        "image/gif",
    ],
    "PDF": ["application/pdf"],
    "Text": [
        "text/plain",
        "text/html",
        "text/css",
        "text/javascript",
        "application/javascript",
        "text/rich-text",
        "text/x-shellscript",
        "text/markdown",
        "application/json",
        "application/x-httpd-php",
        "text/x-python",
        "application/x-python-script",
        "application/x-sql",
        "text/x-perl",
        "text/x-csrc",
        "text/x-sh",
    ],
    "XML Data": ["application/xml"],
    "Document": [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.apple.pages",
        "application/x-abiword",
        "frappe_doc",
    ],
    "Spreadsheet": [
        "application/vnd.ms-excel",
        "link/googlesheets",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
        "text/csv",
        "application/vnd.apple.numbers",
    ],
    "Presentation": [
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.apple.keynote",
    ],
    "Audio": ["audio/mpeg", "audio/wav", "audio/x-midi", "audio/ogg", "audio/mp4", "audio/mp3"],
    "Video": ["video/mp4", "video/webm", "video/ogg", "video/quicktime", "video/x-matroska"],
    "Book": ["application/epub+zip", "application/x-mobipocket-ebook"],
    "Application": [
        "application/octet-stream",
        "application/x-sh",
        "application/vnd.microsoft.portable-executable",
    ],
    "Archive": [
        "application/zip",
        "application/x-rar-compressed",
        "application/x-tar",
        "application/gzip",
        "application/x-bzip2",
    ],
}


def create_user_directory():
    """
    Create user directory on disk, and insert corresponding DriveEntity doc

    :raises FileExistsError: If user directory already exists
    :return: Dictionary containing the document-name and path
    :rtype: frappe._dict
    """
    if frappe.session.user == "Guest":
        return
    # imperative that user dir is created by an owner that has drive_user role
    user_roles = frappe.get_roles(frappe.session.user)
    if "Drive Admin" not in user_roles:
        if "Drive User" not in user_roles:
            raise frappe.PermissionError("You do not have access to Frappe Drive")
    user_directory_name = _get_user_directory_name()
    user_directory_path = Path(frappe.get_site_path("private/files"), user_directory_name)
    user_directory_path.mkdir(exist_ok=True)

    full_name = frappe.get_value("User", frappe.session.user, "full_name")
    user_directory = frappe.get_doc(
        {
            "doctype": "Drive File",
            "name": user_directory_name,
            "title": f"{full_name}'s Drive",
            "is_group": 1,
            "path": user_directory_path,
        }
    )
    user_directory.flags.file_created = True
    # frappe.local.rollback_observers.append(user_directory)
    # (Placeholder) till we make login and onboarding
    # user_directory breaks if its not created by a `drive_user`
    user = frappe.get_doc("User", frappe.session.user)

    user.flags.ignore_permlevel_for_fields = ["roles"]
    user.save(ignore_permissions=True)
    user_directory.insert()
    return frappe._dict({"name": user_directory.name, "path": user_directory.path})


def get_home_folder(team):
    ls = (
        frappe.qb.from_(DriveFile)
        .where(((DriveFile.team == team) & DriveFile.parent_entity.isnull()))
        .select(DriveFile.name, DriveFile.path)
        .run(as_dict=True)
    )
    if not ls:
        error_msg = "This team doesn't exist - please create in Desk."
        team_names = frappe.get_all(
            "Drive Team Member",
            pluck="parent",
            filters=[
                ["parenttype", "=", "Drive Team"],
                ["user", "=", frappe.session.user],
            ],
        )
        if team_names:
            error_msg += f"<br /><br />Or maybe you want <a class='text-black' href='/drive/t/{team_names[0]}'>{frappe.db.get_value('Drive Team', team_names[0], 'title')}</a>?"
        frappe.throw(error_msg, {"error": frappe.NotFound})
    return ls[0]


def get_user_directory(user=None):
    """
    Return the document-name, and path of the specified user's user directory

    :param user: User whose directory details should be returned. Defaults to the current user
    :raises FileNotFoundError: If user directory does not exist
    :return: Dictionary containing the document-name and path
    :rtype: frappe._dict
    """

    user_directory_name = _get_user_directory_name(user)
    user_directory = frappe.db.get_value(
        "Drive File", user_directory_name, ["name", "path"], as_dict=1
    )
    if user_directory is None:
        user_directory = create_user_directory()
    return user_directory


def _get_user_directory_name(user=None):
    """Returns user directory name from user's unique id"""
    if not user:
        user = frappe.session.user
    return hashlib.md5(user.encode("utf-8")).hexdigest()


@frappe.whitelist()
def get_new_title(title, parent_name, folder=False):
    """
    Returns new title for an entity if same title exists for another entity at the same level

    :param entity_title: Title of entity to be renamed (if at all)
    :param parent_entity: Parent entity of entity to be renamed (if at all)
    :return: String with new title
    """
    entity_title, entity_ext = os.path.splitext(title)

    filters = {
        "is_active": 1,
        "parent_entity": parent_name,
        "title": ["like", f"{entity_title}%{entity_ext}"],
    }

    if folder:
        filters["is_group"] = 1

    sibling_entity_titles = frappe.db.get_list(
        "Drive File",
        filters=filters,
        pluck="title",
    )

    if not sibling_entity_titles:
        return title
    return f"{entity_title} ({len(sibling_entity_titles)}){entity_ext}"


def create_user_thumbnails_directory():
    user_directory_name = _get_user_directory_name()
    user_directory_thumnails_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "thumbnails"
    )
    user_directory_thumnails_path.mkdir(exist_ok=True)
    return user_directory_thumnails_path


def get_team_thumbnails_directory(team_name):
    return Path(
        frappe.get_site_path("private/files"), get_home_folder(team_name)["name"], "thumbnails"
    )


def create_thumbnail(entity_name, path, mime_type, team):
    user_thumbnails_directory = get_team_thumbnails_directory(team)
    thumbnail_savepath = Path(user_thumbnails_directory, entity_name + ".thumbnail")

    with DistributedLock(path, exclusive=False):
        if mime_type.startswith("image"):
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    image_path = path
                    with Image.open(image_path).convert("RGB") as image:
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512))
                        image.save(str(thumbnail_savepath), format="webp")
                    break
                except Exception as e:
                    print(e)
                    print(f"Failed to create thumbnail. Retry {retry_count+1}/{max_retries}")
                    retry_count += 1
            else:
                print("Failed to create thumbnail after maximum retries.")

        if mime_type.startswith("video"):
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    video_path = str(path)
                    cap = cv2.VideoCapture(video_path)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    target_frame = int(frame_count / 2)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    ret, frame = cap.read()
                    cap.release()
                    _, thumbnail_encoded = cv2.imencode(
                        # ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30]
                        ".webp",
                        frame,
                        [int(cv2.IMWRITE_WEBP_QUALITY), 50],
                    )
                    with open(str(thumbnail_savepath) + ".thumbnail", "wb") as f:
                        f.write(thumbnail_encoded)
                    break
                except Exception as e:
                    print(f"Failed to create thumbnail. Retry {retry_count+1}/{max_retries}")
                    retry_count += 1
            else:
                print("Failed to create thumbnail after maximum retries.")


def dribble_access(path):
    default_access = {
        "read": 0,
        "comment": 0,
        "share": 0,
        "write": 0,
    }
    result = {}
    for k in path[::-1]:
        for t in default_access.keys():
            if k[t] and not result.get(t):
                result[t] = k[t]
    return {**default_access, **result}


@frappe.whitelist()
def generate_upward_path(entity_name, user=None):
    """
    Given an ID traverse upwards till the root node
    Stops when parent_drive_file IS NULL
    """
    entity = frappe.db.escape(entity_name)
    if not user:
        user = frappe.session.user
    user = frappe.db.escape(user if user != "Guest" else "")

    result = frappe.db.sql(
        f"""WITH RECURSIVE
            generated_path as (
                SELECT
                    `tabDrive File`.title,
                    `tabDrive File`.name,
                    `tabDrive File`.team,
                    `tabDrive File`.parent_entity,
                    `tabDrive File`.is_private,
                    `tabDrive File`.owner,
                    0 AS level
                FROM
                    `tabDrive File`
                WHERE
                    `tabDrive File`.name = {entity}
                UNION ALL
                SELECT
                    t.title,
                    t.name,
                    t.team,
                    t.parent_entity,
                    t.is_private,
                    t.owner,
                    gp.level + 1
                FROM
                    generated_path as gp
                    JOIN `tabDrive File` as t ON t.name = gp.parent_entity
            )
        SELECT
            gp.title,
            gp.name,
            gp.owner,
            gp.parent_entity,
            gp.is_private,
            gp.team,
            p.read,
            p.write,
            p.comment,
            p.share
        FROM
            generated_path  as gp
        LEFT JOIN `tabDrive Permission` as p
        ON gp.name = p.entity AND p.user = {user}
        ORDER BY gp.level DESC;
    """,
        as_dict=1,
    )
    for i, p in enumerate(result):
        print(p, dribble_access(result[: i + 1]))
        result[i] = {**p, **dribble_access(result[: i + 1])}
    print("final", result)
    return result


def get_valid_breadcrumbs(entity, user_access):
    """
    Determine user access and generate upward path (breadcrumbs).
    """
    file_path = generate_upward_path(entity.name)

    # If team/admin of this entity, then entire path
    if user_access.get("type") in ["admin", "team"]:
        return file_path

    # Otherwise, slice where they lose read access.
    lose_access = next((i for i, k in enumerate(file_path[::-1]) if not k["read"]), 0)
    return file_path[-lose_access:]


def update_file_size(entity, delta):
    doc = frappe.get_doc("Drive File", entity)
    while doc.parent_entity:
        doc.file_size += delta
        doc.save(ignore_permissions=True)
        doc = frappe.get_doc("Drive File", doc.parent_entity)
    # Update root
    doc.file_size += delta
    doc.save(ignore_permissions=True)
