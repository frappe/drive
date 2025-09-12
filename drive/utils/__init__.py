import re
from datetime import datetime

import frappe
from bs4 import BeautifulSoup

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
    "Frappe Document": [
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
        "frappe/slides",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.apple.keynote",
    ],
    "Code": [
        "text/x-python",
        "text/html",
        "text/css",
        "text/javascript",
        "application/javascript",
        "text/rich-text",
        "text/x-shellscript",
        "text/markdown",
        "application/json",
        "application/x-httpd-php",
        "application/x-python-script",
        "application/x-sql",
        "text/x-perl",
        "text/x-csrc",
        "text/x-sh",
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


def get_ancestors_of(entity_name):
    """
    Return all parent nodes till the root node
    """
    # CONCAT_WS('/', t.title, gp.path),
    entity_name = frappe.db.escape(entity_name)
    result = frappe.db.sql(
        f"""
        WITH RECURSIVE generated_path as (
        SELECT
            `tabDrive File`.name,
            `tabDrive File`.parent_entity
        FROM `tabDrive File`
        WHERE `tabDrive File`.name = {entity_name}

        UNION ALL

        SELECT
            t.name,
            t.parent_entity
        FROM generated_path as gp
        JOIN `tabDrive File` as t ON t.name = gp.parent_entity)
        SELECT name FROM generated_path;
    """,
        as_dict=0,
    )
    # Match the output of frappe/nested.py get_ancestors_of
    flattened_list = [item for sublist in result for item in sublist]
    flattened_list.pop(0)
    return flattened_list


def dribble_access(path):
    default_access = {
        "read": 0,
        "comment": 0,
        "share": 0,
        "upload": 0,
        "write": 0,
    }
    result = {}
    for k in path[::-1]:
        for t in default_access.keys():
            if k[t] and not result.get(t):
                result[t] = k[t]
    return {**default_access, **result}


def generate_upward_path(entity_name, user=None):
    """
    Given an ID traverse upwards till the root node
    Stops when parent_drive_file IS NULL
    """
    entity = frappe.db.escape(entity_name)
    if user is None:
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
            p.upload,
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
        result[i] = {**p, **dribble_access(result[: i + 1])}
    return result


def get_valid_breadcrumbs(user_access, paths, is_private=None):
    """
    Determine user access and generate upward path (breadcrumbs).
    """
    # If team/admin of this entity, then entire path
    if user_access.get("type") in ["admin", "team", "team-admin"]:
        return paths[0]

    # Otherwise, slice where they lose read access.
    try:
        lose_access = max(
            next((i for i, k in enumerate(path[::-1]) if not k["read"]), 0)
            for path in paths
            if path
        )
        return paths[0][-lose_access:]
    except:
        return paths[0] if len(paths) else []


def get_file_type(r):
    if r["is_group"]:
        return "Folder"
    elif r["is_link"]:
        return "Link"
    else:
        try:
            return next(k for (k, v) in MIME_LIST_MAP.items() if r["mime_type"] in v)
        except StopIteration:
            return "Unknown"


def update_file_size(entity, delta):
    doc = frappe.get_doc("Drive File", entity)
    while doc.parent_entity:
        doc.file_size += delta
        doc.save(ignore_permissions=True)
        doc = frappe.get_doc("Drive File", doc.parent_entity)
    # Update root
    doc.file_size += delta
    doc.save(ignore_permissions=True)


def if_folder_exists(team, folder_name, parent, personal):
    values = {
        "title": folder_name,
        "is_group": 1,
        "is_active": 1,
        "team": team,
        "owner": frappe.session.user,
        "is_private": personal,
        "parent_entity": parent,
    }
    existing_folder = frappe.db.get_value(
        "Drive File", values, ["name", "title", "is_group", "is_active"], as_dict=1
    )

    if existing_folder:
        return existing_folder.name
    else:
        d = frappe.get_doc({"doctype": "Drive File", **values, "_modified": datetime.now()})
        d.insert()
        return d.name


def create_drive_file(
    team,
    is_private,
    title,
    parent,
    mime_type,
    entity_path,
    file_size=0,
    last_modified=None,
    document=None,
    is_group=False,
    owner=None,
):
    drive_file = frappe.get_doc(
        {
            "doctype": "Drive File",
            "team": team,
            "is_private": is_private,
            "title": title,
            "parent_entity": parent,
            "file_size": file_size,
            "mime_type": mime_type,
            "document": document,
            "is_group": is_group,
            "_modified": (
                datetime.fromtimestamp(last_modified) if last_modified else datetime.now()
            ),
        }
    )
    drive_file.flags.file_created = True
    drive_file.insert(ignore_permissions=True)
    path = entity_path(drive_file)
    drive_file.path = str(path) if path else ""
    drive_file.save(ignore_permissions=True)
    if owner:
        drive_file.db_set("owner", owner, update_modified=False)
    return drive_file


def extract_mentions(content):
    soup = BeautifulSoup(content, "html.parser")
    mentions = []
    for span in soup.find_all("span", class_="mention", attrs={"data-type": "mention"}):
        data_id = span.get("data-id")
        if data_id:
            mentions.append(data_id)
    return mentions


def strip_comment_spans(html: str) -> str:
    """
    Remove only <span> tags with a data-comment-id attribute.
    Keeps their inner content.
    """
    soup = BeautifulSoup(html, "html.parser")

    for span in soup.find_all("span", attrs={"data-comment-id": True}):
        span.unwrap()
    for span in soup.find_all("img"):
        span.unwrap()

    return str(soup)


def get_default_team():
    return frappe.get_value("Drive Team", {"owner": frappe.session.user, "personal": 1}, "name")


def default_team(func):
    def wrapper(*args, **kwargs):
        # Handle weird frappe thing
        if "cmd" in kwargs:
            kwargs.pop("cmd")
        if not kwargs.get("team"):
            kwargs["team"] = get_default_team()
        return func(*args, **kwargs)

    return wrapper
