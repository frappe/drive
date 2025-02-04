"""
Migration script for data from old Drive structure to new Drive structure
"""

import json


def json_serial(obj):
    from datetime import datetime, date

    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


# Writing
with open("/Users/cafwan/Documents/drive_prod.json", "w") as f:
    json.dump(
        [frappe.get_doc("Drive Entity", d).as_dict() for d in frappe.get_list("Drive Entity")],
        f,
        default=json_serial,
    )

with open("/Users/cafwan/Documents/drive_prod_p.json", "w") as f:
    json.dump(
        [frappe.get_doc("Drive DocShare", d).as_dict() for d in frappe.get_list("Drive DocShare")],
        f,
        default=json_serial,
    )

# Loading file
with open("/Users/cafwan/Documents/drive_prod.json") as f:
    l = json.load(f)

with open("/Users/cafwan/Documents/drive_prod_p.json") as f:
    p = json.load(f)

# Loading into DB
for k in l:
    if not k["parent_drive_entity"]:
        continue
    path = ""
    if k["path"]:
        no = 8 if k["path"].startswith("/home") else 4
        path = "0194d038-0089-78f2-bcaa-8fdfb4287873/" + "/".join(k["path"].split("/")[no:])
    try:
        frappe.get_doc(
            {
                "doctype": "Drive Entity",
                **k,
                "parent_entity": None,
                "document": "",
                "team": "0194d037-a46c-7800-9118-950d2cbb54a2",
                "path": path,
            }
        ).insert()
    except BaseException as b:
        print("An error occurred", b)
        continue
frappe.db.commit()

for k in l:
    if not k["parent_drive_entity"]:
        continue
    try:
        d = frappe.get_doc("Drive Entity", k["name"])
        d.parent_entity = k["parent_drive_entity"]
        d.save()
    except:
        pass
frappe.db.commit()

for k in p:
    if k["share_doctype"] != "Drive Entity" or k["everyone"] or k["user_doctype"] == "User Group":
        continue

    try:
        if "name" in k:
            k.pop("name")
        frappe.get_doc(
            {
                **k,
                "doctype": "Drive Permission",
                "user": k["user_name"],
                "comment": 1,
                "entity": k["share_name"],
            }
        ).insert()
    except BaseException as b:
        print("An error occurred", b)
        continue
