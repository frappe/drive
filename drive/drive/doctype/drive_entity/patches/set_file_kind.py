import frappe


def mime_to_human(mime_type, is_group):
    """
    mimetype to human-readable formats
    less descriptive by design, used for filtering
    """
    mime_dict = {
        # Image
        "image/png": "Image",
        "image/jpeg": "Image",
        "image/svg+xml": "Image",
        "image/heic": "Image",
        "image/heif": "Image",
        "image/avif": "Image",
        "image/webp": "Image",
        "image/tiff": "Image",
        "image/gif": "Image",
        # PDF
        "application/pdf": "PDF",
        # Text
        "text/plain": "Text",
        "text/html": "Text",
        "text/css": "Text",
        "text/javascript": "Text",
        "application/javascript": "Text",
        "text/rich-text": "Text",
        "text/x-shellscript": "Text",
        "text/markdown": "Text",
        "application/json": "Text",
        "application/xml": "XML Data",
        "application/x-httpd-php": "Text",
        "text/x-python": "Text",
        "application/x-python-script": "Text",
        "application/x-sql": "Text",
        "text/x-perl": "Text",
        "text/x-csrc": "Text",
        "text/x-sh": "Text",
        # Document
        "application/msword": "Document",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Document",
        "application/vnd.oasis.opendocument.text": "Document",
        "application/vnd.apple.pages": "Document",
        "application/x-abiword": "Document",
        "frappe_doc": "Document",
        "frappe_whiteboard": "Whiteboard",
        # Spreadsheet
        "application/vnd.ms-excel": "Spreadsheet",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Spreadsheet",
        "application/vnd.oasis.opendocument.spreadsheet": "Spreadsheet",
        "text/csv": "Spreadsheet",
        "application/vnd.apple.numbers": "Spreadsheet",
        # Presentation
        "application/vnd.ms-powerpoint": "Presentation",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "Presentation",
        "application/vnd.oasis.opendocument.presentation": "Presentation",
        "application/vnd.apple.keynote": "Presentation",
        # Audio
        "audio/mpeg": "Audio",
        "audio/wav": "Audio",
        "audio/x-midi": "Audio",
        "audio/ogg": "Audio",
        "audio/mp4": "Audio",
        "audio/mp3": "Audio",
        # Video
        "video/mp4": "Video",
        "video/webm": "Video",
        "video/ogg": "Video",
        "video/quicktime": "Video",
        "video/x-matroska": "Video",
        # Book
        "application/epub+zip": "Book",
        "application/x-mobipocket-ebook": "Book",
        # Application
        "application/octet-stream": "Application",
        "application/x-sh": "Application",
        "application/vnd.microsoft.portable-executable": "Application",
        # Archive
        "application/zip": "Archive",
        "application/x-rar-compressed": "Archive",
        "application/x-tar": "Archive",
        "application/gzip": "Archive",
        "application/x-bzip2": "Archive",
    }
    if is_group:
        return "Folder"
    else:
        mime_type_lower = mime_type.lower()
        return mime_dict.get(mime_type_lower, "Unknown")


def execute():
    all_entities = frappe.db.get_all(
        "Drive Entity", fields=["name", "mime_type", "file_kind", "is_group"]
    )
    for i in all_entities:
        eval = mime_to_human(i.mime_type, i.is_group)
        frappe.db.set_value("Drive Entity", i.name, "file_kind", eval, update_modified=False)
