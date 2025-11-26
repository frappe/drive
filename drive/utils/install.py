from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_custom_file_fields()


def create_custom_file_fields():
    create_custom_fields(
        {
            "File": [
                {
                    "fieldname": "drive_tab",
                    "fieldtype": "Tab Break",
                    "label": "Drive",
                    "insert_after": "uploaded_to_google_drive",
                },
                {
                    "label": "Team",
                    "fieldname": "team",
                    "fieldtype": "Link",
                    "options": "Drive Team",
                    "insert_after": "drive_tab",
                },
                {
                    "label": "Path",
                    "fieldname": "path",
                    "fieldtype": "Long Text",
                    "insert_after": "team",
                },
                {
                    "label": "MIME Type",
                    "fieldname": "mime_type",
                    "fieldtype": "Data",
                    "insert_after": "path",
                },
                {
                    "label": "Link",
                    "fieldname": "link",
                    "fieldtype": "Data",
                    "insert_after": "mime_type",
                },
                {
                    "label": "Active",
                    "fieldname": "active",
                    "fieldtype": "Int",
                    "default": 1,
                    "insert_after": "link",
                },
                {
                    "label": "Settings",
                    "fieldname": "settings",
                    "fieldtype": "JSON",
                    "insert_after": "active",
                },
                {
                    "label": "Modified",
                    "fieldname": "_modified",
                    "fieldtype": "Datetime",
                    "insert_after": "settings",
                },
            ]
        }
    )
