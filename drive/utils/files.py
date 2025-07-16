import frappe
import os
from pathlib import Path
from PIL import Image, ImageOps
from drive.locks.distributed_lock import DistributedLock
import cv2
from pathlib import Path
import os
import boto3
import frappe
from io import BytesIO
from botocore.config import Config


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


class FileManager:
    ACCEPTABLE_MIME_TYPES = [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
    ]

    def __init__(self):
        settings = frappe.get_single("Drive S3 Settings")
        self.s3_enabled = settings.enabled
        self.bucket = settings.bucket
        self.site_folder = Path(frappe.get_site_path("private/files"))
        if self.s3_enabled:
            self.conn = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_key,
                aws_secret_access_key=settings.get_password("aws_secret"),
                endpoint_url=(settings.endpoint_url or None),
                config=Config(signature_version=settings.signature_version),
            )

    def can_create_thumbnail(self, file):
        # Don't create thumbnails for text files
        return (
            file.mime_type.startswith(("image", "video"))
            or file.mime_type == "application/pdf"
            or file.mime_type in FileManager.ACCEPTABLE_MIME_TYPES
        )

    def upload_file(self, current_path: str, new_path: str, drive_file: str = None) -> None:
        """
        Moves the file from the current path to another path
        """
        if self.s3_enabled:
            self.conn.upload_file(current_path, self.bucket, new_path)
            if drive_file and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=current_path,
                )
            else:
                os.remove(current_path)
        else:
            os.rename(current_path, self.site_folder / new_path)
            if drive_file and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=str(self.site_folder / new_path),
                )

    def upload_thumbnail(self, file, file_path: str):
        """
        Creates a thumbnail for the file on disk and then uploads to the relevant team directory
        """
        team_directory = get_home_folder(file.team)["name"]
        save_path = Path(team_directory) / "thumbnails" / (file.name + ".png")
        disk_path = str((self.site_folder / save_path).resolve())

        with DistributedLock(file.path, exclusive=False):
            try:
                # Keep image/video thumbnail as `thumbnail` results in very dark thumbnails (albeit better)
                if file.mime_type.startswith("image"):
                    with Image.open(file_path).convert("RGB") as image:
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512))
                        image.save(str(disk_path), format="webp")
                elif file.mime_type.startswith("video"):
                    cap = cv2.VideoCapture(file_path)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    target_frame = int(frame_count / 2)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    _, frame = cap.read()
                    cap.release()
                    _, thumbnail_encoded = cv2.imencode(
                        ".webp",
                        frame,
                        [int(cv2.IMWRITE_WEBP_QUALITY), 50],
                    )
                    with open(disk_path, "wb") as f:
                        f.write(thumbnail_encoded)
                else:
                    from thumbnail import generate_thumbnail

                    # Word document thumbnail
                    generate_thumbnail(
                        file_path,
                        disk_path,
                        {
                            "trim": False,
                            "height": 512,
                            "width": 512,
                            "quality": 100,
                            "type": "thumbnail",
                        },
                    )
                final_path = Path(disk_path)
                if self.s3_enabled:
                    os.remove(file_path)
                    self.conn.upload_file(
                        final_path, self.bucket, str(save_path.with_suffix(".thumbnail"))
                    )
                    final_path.unlink()
                else:
                    final_path.rename(final_path.with_suffix(".thumbnail"))

            except Exception:
                if self.s3_enabled:
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass

    def get_file(self, path):
        """
        Function to read file from a s3 file.

        Temporary: if not found in S3, look at disk.
        """
        if self.s3_enabled:
            try:
                buf = self.conn.get_object(Bucket=self.bucket, Key=path)["Body"]
            except:
                return ""
        else:
            with DistributedLock(path, exclusive=False):
                with open(self.site_folder / path, "rb") as fh:
                    buf = BytesIO(fh.read())

        return buf

    def get_thumbnail_path(self, team, name):
        return Path(get_home_folder(team)["name"]) / "thumbnails" / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(str(self.get_thumbnail_path(team, name)))

    def delete_file(self, team, name, path):
        if self.s3_enabled:
            self.conn.delete_object(Bucket=self.bucket, Key=path)
        else:
            try:
                (self.site_folder / path).unlink()
                self.get_thumbnail_path(team, name).unlink()
            except FileNotFoundError:
                pass


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


@frappe.whitelist()
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
        d = frappe.get_doc({"doctype": "Drive File", **values})
        d.insert()
        return d.name
