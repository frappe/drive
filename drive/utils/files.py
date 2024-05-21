import frappe
import os
import mimetypes
from pathlib import Path
import hashlib
from PIL import Image, ImageOps
from drive.locks.distributed_lock import DistributedLock
import cv2


def create_user_directory():
    """
    Create user directory on disk, and insert corresponding DriveEntity doc

    :raises FileExistsError: If user directory already exists
    :return: Dictionary containing the document-name and path
    :rtype: frappe._dict
    """
    if frappe.session.user == "Guest":
        return
    user_directory_name = _get_user_directory_name()
    user_directory_path = Path(frappe.get_site_path("private/files"), user_directory_name)
    user_directory_path.mkdir(exist_ok=True)

    full_name = frappe.get_value("User", frappe.session.user, "full_name")
    user_directory = frappe.get_doc(
        {
            "doctype": "Drive Entity",
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
    user.add_roles("Drive User")
    user.save(ignore_permissions=True)
    user_directory.insert()
    return frappe._dict({"name": user_directory.name, "path": user_directory.path})


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
        "Drive Entity", user_directory_name, ["name", "path"], as_dict=1
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
def get_new_title(title, parent_name, document=False, folder=False):
    """
    Returns new title for an entity if same title exists for another entity at the same level

    :param entity_title: Title of entity to be renamed (if at all)
    :param parent_entity: Parent entity of entity to be renamed (if at all)
    :return: String with new title
    """
    entity_title, entity_ext = os.path.splitext(title)

    filters = {
        "is_active": 1,
        "parent_drive_entity": parent_name,
        "title": ["like", f"{entity_title}%{entity_ext}"],
    }

    if entity_ext:
        mime_type = mimetypes.guess_type(title)
        filters["mime_type"] = mime_type[0]

    if document:
        mime_type = "frappe_doc"

    if folder:
        filters["is_group"] = 1

    sibling_entity_titles = frappe.db.get_list(
        "Drive Entity",
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


def get_user_thumbnails_directory(user=None):
    user_directory_name = _get_user_directory_name(user)
    user_directory_thumnails_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "thumbnails"
    )
    if not os.path.exists(user_directory_thumnails_path):
        try:
            user_directory_thumnails_path = create_user_thumbnails_directory()
        except FileNotFoundError:
            user_directory_thumnails_path = create_user_thumbnails_directory()
    return user_directory_thumnails_path


def create_thumbnail(entity_name, path, mime_type):
    user_thumbnails_directory = None
    try:
        user_thumbnails_directory = get_user_thumbnails_directory()
    except FileNotFoundError:
        user_thumbnails_directory = create_user_thumbnails_directory()

    thumbnail_savepath = Path(user_thumbnails_directory, entity_name)
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
                        image.save(str(thumbnail_savepath) + ".thumbnail", format="webp")
                    break
                except Exception as e:
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
