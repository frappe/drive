# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from pathlib import Path
import shutil
from drive.utils.files import get_home_folder


class DriveTeam(Document):
    def on_update(self):
        """Creates the file on disk"""
        DriveFile = frappe.qb.DocType("Drive File")
        if (
            frappe.qb.from_(DriveFile)
            .where(((DriveFile.team == self.name) & DriveFile.parent_entity.isnull()))
            .select(DriveFile.name, DriveFile.path)
            .run(as_dict=True)
        ):
            return
        d = frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": f"Drive - {self.name}",
                "is_group": 1,
                "team": self.name,
            }
        )
        d.insert()

        user_directory_path = Path(frappe.get_site_path("private/files"), d.name)
        user_directory_path.mkdir()
        (user_directory_path / "uploads").mkdir()
        (user_directory_path / "embeds").mkdir()
        (user_directory_path / "thumbnails").mkdir()
        d.path = d.name
        d.save()

    def on_trash(self):
        try:
            d = get_home_folder(self.name)
            user_directory_path = Path(frappe.get_site_path("private/files"), d.path)
            shutil.rmtree(str(user_directory_path))
        except FileNotFoundError:
            pass
        frappe.db.delete("Drive File", {"team": self.name})
        frappe.db.commit()


@frappe.whitelist()
def change_team_name(team_id, new_name):
    """
    Phiên bản đơn giản chỉ kiểm tra membership
    """
    try:
        user_id = frappe.session.user

        if not new_name or not new_name.strip():
            frappe.throw(_("Tên nhóm không được để trống."))

        is_member = check_permission_user_update(team_id, user_id)

        if not is_member:
            frappe.throw(_("Bạn không có quyền thay đổi tên nhóm này."))

        team = frappe.get_doc("Drive Team", team_id)
        team.title = new_name.strip()
        team.save()

        frappe.msgprint(_("Đã cập nhật tên nhóm thành công."))

    except frappe.ValidationError as e:
        frappe.msgprint(_("Lỗi: {0}").format(e))


@frappe.whitelist()
def check_permission_user_update(team_id, user_id):
    is_member = frappe.db.exists(
        "Drive Team Member", {"parent": team_id, "user": user_id, "access_level": 2}
    )
    if not is_member:
        return False
    return True
