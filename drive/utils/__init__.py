import os
import inspect
from datetime import datetime
from functools import wraps
from pathlib import Path

import frappe
from bs4 import BeautifulSoup
from pypika import Field, functions as fn
import mimemapper

DriveFile = frappe.qb.DocType("File")
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


FILE_FIELDS = [
    "name",
    "file_name",
    "folder",
    "file_url",
    "file_size",
    "file_type",
    "is_folder",
    "details_doctype",
    "details_docname",
    "team",
    "creation",
    fn.Coalesce(Field("file_modified"), DriveFile.modified).as_("modified"),
    "owner",
    "is_drive_file",
]


def get_home_folder(team):
    ls = (
        frappe.qb.from_(DriveFile)
        .where(((DriveFile.team == team) & DriveFile.folder.isnull()))
        .select(DriveFile.name, DriveFile.file_url)
        .run(as_dict=True)
    )
    if not ls:
        error_msg = f"This team doesn't exist."
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
        if not team_names:
            error_msg += f"<br /><br />Please <a class='text-black' href='/drive/setup'>setup</a> an account."
        frappe.throw(error_msg)
    return ls[0]


def get_ancestors_of(entity_name):
    """
    Return all parent nodes till the root node
    """
    result = frappe.db.sql(
        """
        WITH RECURSIVE generated_path as (
        SELECT
            `tabFile`.name,
            `tabFile`.folder
        FROM `tabFile`
        WHERE `tabFile`.name = %(entity_name)s

        UNION ALL

        SELECT
            t.name,
            t.folder
        FROM generated_path as gp
        JOIN `tabFile` as t ON t.name = gp.folder)
        SELECT name FROM generated_path;
    """,
        values={"entity_name": entity_name},
        as_dict=0,
    )
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
        "shared_team": None,
    }
    result = {}
    for k in path[::-1]:
        for t in default_access.keys():
            if k[t] and not result.get(t):
                result[t] = k[t]
    return {**default_access, **result}


def generate_upward_path(entity_name, user=None, team=0):
    """
    Given an ID traverse upwards till the root node
    Stops when parent_drive_file IS NULL
    """
    if user is None:
        user = frappe.session.user
    user = frappe.db.escape(user if user != "Guest" else "")

    filter_: str
    if team:
        filter_ = "p.team = 1"
    else:
        filter_ = f"p.user = {user}"

    result = frappe.db.sql(
        f"""WITH RECURSIVE
            generated_path as (
                SELECT
                    `tabFile`.file_name,
                    `tabFile`.name,
                    `tabFile`.team,
                    `tabFile`.folder,
                    `tabFile`.owner,
                    0 AS level
                FROM
                    `tabFile`
                WHERE
                    `tabFile`.name = %(entity_name)s
                UNION ALL
                SELECT
                    t.file_name,
                    t.name,
                    t.team,
                    t.folder,
                    t.owner,
                    gp.level + 1
                FROM
                    generated_path as gp
                    JOIN `tabFile` as t ON t.name = gp.folder
            )
        SELECT
            gp.file_name,
            gp.name,
            gp.owner,
            gp.folder,
            gp.team,
            p.read,
            p.upload,
            p.user AS shared_team,
            p.write,
            p.comment,
            p.share
        FROM
            generated_path  as gp
        LEFT JOIN `tabDrive Permission` as p
        ON gp.name = p.entity AND {filter_}
        ORDER BY gp.level DESC;
    """,
        values={"entity_name": entity_name},
        as_dict=1,
    )
    for i, p in enumerate(result):
        result[i] = {**p, **dribble_access(result[: i + 1])}
    return result


def get_valid_breadcrumbs(entity_name, user_access):
    """
    Determine user access and generate upward path (breadcrumbs).
    """
    # If team/admin of this entity, then entire path
    paths = [generate_upward_path(entity_name)]
    if user_access.get("type") in ["admin", "user"]:
        return paths[0]
    paths.append(generate_upward_path(entity_name, team=1))
    paths.append(generate_upward_path(entity_name, user="Guest"))

    # Otherwise, slice where they lose read access.
    try:
        lose_access = max(next((i for i, k in enumerate(path[::-1]) if not k["read"]), 0) for path in paths if path)
        return paths[0][-lose_access:]
    except:
        frappe.log_error("Breadcrumbs errored out", (entity_name, user_access, frappe.session.user, paths))
        return paths[0] if len(paths) else []


def get_file_type(mime_type):
    try:
        return next(k for (k, v) in MIME_LIST_MAP.items() if mime_type in v)
    except StopIteration:
        return "Unknown"


def update_file_size(entity, delta):
    doc = frappe.get_doc("File", entity)
    while doc.folder:
        doc.file_size += delta
        doc.save(ignore_permissions=True)
        doc = frappe.get_doc("File", doc.folder)
    # Update root
    doc.file_size += delta
    doc.save(ignore_permissions=True)


def if_folder_exists(team, folder_name, parent):
    values = {
        "file_name": folder_name,
        "is_folder": 1,
        "status": 1,
        "team": team,
        "folder": parent,
    }
    existing_folder = frappe.db.get_value("File", values, ["name", "file_name", "is_folder", "status"], as_dict=1)

    if existing_folder:
        return existing_folder.name
    else:
        d = frappe.get_doc({"doctype": "File", **values, "file_modified": frappe.utils.now_datetime()})
        d.insert()
        return d.name


def create_drive_file(
    team,
    file_name,
    parent,
    file_type,
    entity_path,
    mime_type=None,
    file_size=0,
    file_modified=None,
    document=None,
    owner=None,
):
    drive_file = frappe.get_doc(
        {
            "doctype": "File",
            "is_drive_file": 1,
            "is_private": 1,
            "team": team,
            "file_name": file_name,
            "folder": parent,
            "file_size": file_size,
            "file_type": file_type,
            "mime_type": mime_type,
            "doc": document,
            "is_folder": file_type == "Folder",
            "file_modified": (datetime.fromtimestamp(file_modified) if file_modified else frappe.utils.now()),
        }
    )
    drive_file.flags.file_created = True
    drive_file.insert(ignore_permissions=True)
    path = entity_path if isinstance(entity_path, str) else entity_path(drive_file)
    drive_file.file_url = str(path) if path else ""
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


@frappe.whitelist()
def get_default_team(with_file: bool = False):
    default_team = frappe.get_value("Drive Team", {"owner": frappe.session.user, "personal": 1}, "name")
    if with_file:
        file = get_home_folder(default_team)
        return {"team": default_team, "file": file.name}
    return default_team


def default_team(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Handle weird frappe thing
        if "cmd" in kwargs:
            kwargs.pop("cmd")

        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        if (
            "team" not in bound_args.arguments
            or not bound_args.arguments["team"]
            or bound_args.arguments["team"] == "home"
        ):
            kwargs["team"] = get_default_team()
        return func(*args, **kwargs)

    return wrapper


# Copied over to avoid circular import
def get_teams(user=None, details=None, exclude_personal=True):
    """
    Returns all the teams that the current user is part of.
    """
    if not user:
        user = frappe.session.user

    teams = frappe.get_all(
        "Drive Team Member",
        pluck="parent",
        filters=[["parenttype", "=", "Drive Team"], ["user", "=", user]],
    )
    if details:
        teams_info = {team: frappe.get_doc("Drive Team", team) for team in teams}
        if exclude_personal:
            return {t: team for t, team in teams_info.items() if not team.personal}
        return teams_info
    return teams

def get_new_file_name(file_name: str, parent_name: str, type: str = False, entity: str | None = None):
    entity_title, entity_ext = os.path.splitext(file_name)

    filters = {
        "status": 1,
        "folder": parent_name,
        "file_name": ["like", f"{entity_title}%{entity_ext}"],
    }

    if type:
        filters["file_type"] = type

    sibling_entity_titles = frappe.db.get_list(
        "File",
        filters=filters,
        fields=["file_name", "name"],
    )
    if (
        not sibling_entity_titles
        or (sibling_entity_titles[0].name == entity)
        or not any(k["file_name"] == file_name for k in sibling_entity_titles)
    ):
        return file_name
    return f"{entity_title} ({len(sibling_entity_titles)}){entity_ext}"


def validate_filename(file_name, parent, type, error=None):
    suggested_name = get_new_file_name(file_name, parent, type)
    if suggested_name != file_name:
        if not error:
            error = f"{file_name} exists."
        frappe.throw(
            f"{error} Try {suggested_name}",
            frappe.ValidationError,
        )


def map_ff_to_drive_type(file):
    if file.is_folder:
        return "Folder"
    mime_type = mimemapper.get_mime_type(file.file_type) if file.file_type else ""
    try:
        return next(k for (k, v) in MIME_LIST_MAP.items() if mime_type in v)
    except StopIteration:
        return "Unknown"


def get_upload_path(team_path, file_name):
    uploads_path = Path(frappe.get_site_path(team_path), ".uploads")
    if not os.path.exists(uploads_path):
        uploads_path.mkdir()
    return uploads_path / file_name
