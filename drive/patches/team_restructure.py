import frappe
from pathlib import Path
import shutil


def execute():
    print(
        "This migration to an alpha release might CORRUPT your data. Do NOT run this before taking a complete backup. You have one minute left to cancel this deployment. "
    )
    input("Are you sure you want to proceed? (Click enter) ")

    frappe.reload_doc("Drive", "doctype", "Drive Team Member")
    frappe.reload_doc("Drive", "doctype", "Drive Team")
    frappe.reload_doc("Drive", "doctype", "Drive File")
    frappe.reload_doc("Drive", "doctype", "Drive Permission")
    if frappe.db.get_list("Drive Team"):
        print("A Drive Team already exists, going ahead might corrupt your database.")
        return

    frappe.db.delete("Drive Team")
    frappe.db.delete("Drive File")
    frappe.db.delete("Drive Permission")
    team = frappe.get_doc({"doctype": "Drive Team", "title": "Frappe"})
    team.insert()

    home_folder = frappe.db.get_list("Drive File", {"team": team.name})[0].name
    entities = frappe.db.get_all("Drive Entity", fields=["*"])
    homes = []
    translate = {}

    for k in entities:
        try:
            if not k["parent_drive_entity"]:
                homes.append(k["name"])
                continue
            k["old_name"] = k.pop("name")
            doc = frappe.get_doc(
                {"doctype": "Drive File", **k, "team": team.name, "is_private": 1}
            )
            if k["path"]:
                path_els = k["path"].split("/")
                doc.path = home_folder + "/" + "/".join(path_els[path_els.index("files") + 2 :])
                p = Path(k["path"])
                try:
                    shutil.copy(
                        str(p), str(Path(frappe.get_site_path("private/files")) / doc.path)
                    )
                except:
                    print(
                        "Moving failed for",
                        str(p),
                        "->",
                        Path(frappe.get_site_path("private/files")) / (doc.path),
                    )
            doc.insert()

            translate[k["old_name"]] = doc.name
        except Exception as e:
            print(f"{k['title']} failed, with:", e)
    frappe.db.commit()

    for k in entities:
        if not k.get("old_name") in translate:
            continue
        name = translate[k["old_name"]]
        frappe.db.set_value("Drive File", name, "owner", k["owner"], update_modified=False)
        frappe.db.set_value("Drive File", name, "creation", k["creation"], update_modified=False)
        frappe.db.set_value("Drive File", name, "modified", k["modified"], update_modified=False)
        frappe.db.set_value(
            "Drive File", name, "modified_by", k["modified_by"], update_modified=False
        )
        if k["parent_drive_entity"] in homes:
            frappe.db.set_value(
                "Drive File",
                name,
                "parent_entity",
                home_folder,
                update_modified=False,
            )
        else:
            frappe.db.set_value(
                "Drive File",
                name,
                "parent_entity",
                translate[k["parent_drive_entity"]],
                update_modified=False,
            )

    shares = frappe.get_list("Drive DocShare", fields=["*"])
    for s in shares:
        entity = translate.get(s["share_name"])
        if not entity:
            continue
        elif s["everyone"]:
            frappe.db.set_value(
                "Drive File",
                entity,
                "is_private",
                0,
                update_modified=False,
            )
        else:
            frappe.get_doc(
                {
                    "doctype": "Drive Permission",
                    "user": "" if s.public else s.user_name,
                    "entity": entity,
                    "read": s["read"],
                    "share": s["share"],
                    "write": s["share"],
                    "comment": 1,
                    "valid_until": s["valid_until"],
                }
            ).insert()

    RENAME_MAP = {
        "Drive Notification": "notif_doctype_name",
        "Drive Favourite": "entity",
        "Drive Document Version": "parent_entity",
        "Drive Entity Activity Log": "entity",
        "Drive Entity Log": "entity_name",
    }

    for doctype, field in RENAME_MAP.items():
        for k in frappe.get_list(doctype, fields=["name", field]):
            if k[field] not in translate:
                continue
            frappe.db.set_value(
                doctype,
                k["name"],
                field,
                translate[k[field]],
                update_modified=False,
            )
