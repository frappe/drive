import frappe
from frappe.utils.telemetry import capture as _capture

APP = "drive"

# Keyed by doctype. A dict value fires only when the field changes to a specific value.
FIELD_CHANGE_EVENTS = {
    "Drive File": {
        "is_active": {
            0: "drive_file_trashed",
            1: "drive_file_restored",
        },
    },
    "Drive User Invitation": {
        "status": {
            "Accepted": "drive_invite_accepted",
            "Expired": "drive_invite_rejected",
        },
    },
}

# Maps full API method paths to event names; matched in after_request.
REQUEST_EVENTS = {
    "drive.api.product.signup": "drive_user_signed_up",
    "drive.api.product.verify_otp": "drive_user_logged_in",
    "drive.api.files.upload_file": "drive_file_uploaded",
    "drive.api.files.create_document_entity": "drive_document_created",
    "drive.api.files.create_folder": "drive_folder_created",
    "drive.api.files.create_link": "drive_link_created",
    "drive.api.files.update_access": "drive_file_shared",
    "drive.api.files.get_file_content": "drive_file_downloaded",
    "drive.api.files.delete_entities": "drive_file_deleted_permanently",
    "drive.api.files.rename": "drive_file_renamed",
    "drive.api.files.move": "drive_file_moved",
    "drive.api.files.search": "drive_file_searched",
    "drive.api.product.create_team": "drive_team_created",
    "drive.api.product.invite_users": "drive_user_invited",
    "drive.api.files.set_favourite": "drive_favourite_set",
}


def on_insert(doc, method=None):
    pass


def on_update(doc, method=None):
    config = FIELD_CHANGE_EVENTS.get(doc.doctype, {})
    if not config:
        return
    for field, event in config.items():
        if field == "*":
            _capture(event, APP)
        elif doc.has_value_changed(field):
            if isinstance(event, dict):
                event_name = event.get(getattr(doc, field))
                if event_name:
                    _capture(event_name, APP)
            else:
                _capture(event, APP)


def on_trash(doc, method=None):
    pass


def after_request(request=None, response=None):
    try:
        _capture('yooo', APP)
        if not hasattr(frappe, "local") or not hasattr(frappe.local, "request"):
            return
        # if frappe.local.request.method != "POST":
        #     return
        path = frappe.local.request.path
        for method, event in REQUEST_EVENTS.items():
            # print('heyy')
            # if not path.endswith(method):
            #     continue
            if method == "drive.api.files.get_file_content":
                pass
                # if not frappe.form_dict.get("trigger_download"):
                #     return
            elif method == "drive.api.files.update_access":
                if frappe.form_dict.get("method") != "share":
                    return
            elif method == "drive.api.files.set_favourite":
                if frappe.form_dict.get("clear_all"):
                    return
                entities = frappe.form_dict.get("entities") or []
                if isinstance(entities, str):
                    import json
                    try:
                        entities = json.loads(entities)
                    except Exception:
                        return
                if not any(
                    isinstance(e, dict) and e.get("is_favourite")
                    for e in entities
                ):
                    return
            _capture(event, APP)
            print('captured', event)
            return
    except Exception:
        pass
