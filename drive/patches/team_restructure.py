import frappe


def execute():
    frappe.reload_doc("Drive", "doctype", "Drive Team Member")
    frappe.reload_doc("Drive", "doctype", "Drive Team")
    frappe.reload_doc("Drive", "doctype", "Drive File")
    frappe.reload_doc("Drive", "doctype", "Drive Permission")

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
                homes.append(doc.name)
                continue
            k["old_name"] = k.pop("name")
            doc = frappe.get_doc({"doctype": "Drive File", **k, "team": team.name})
            if k["path"]:
                path_els = k["path"].split("/")
                doc.path = home_folder + "/" + "/".join(path_els[path_els.index("files") + 2 :])
            doc.insert()
            translate[k["old_name"]] = doc.name
        except Exception as e:
            print(f"{k["title"]} failed, with:", e)

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
                k["parent_drive_entity"],
                update_modified=False,
            )

    shares = frappe.get_list("Drive DocShare", fields=["*"])
    for s in shares:
        if s["everyone"] or not s["share_name"] in translate:
            continue
        else:
            frappe.get_doc(
                {
                    "doctype": "Drive Permission",
                    "user": "" if s.public else s.user_name,
                    "entity": translate[s["share_name"]],
                    "read": s["read"],
                    "share": s["share"],
                    "write": s["share"],
                    "comment": 1,
                    "valid_until": s["valid_until"],
                }
            ).insert()
