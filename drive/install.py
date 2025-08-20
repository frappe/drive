import frappe


def after_install():
    index_check = frappe.db.sql(
        """SHOW INDEX FROM `tabDrive File` WHERE Key_name = 'drive_file_title_fts_idx'"""
    )
    if not index_check:
        frappe.db.sql(
            """ALTER TABLE `tabDrive File` ADD FULLTEXT INDEX drive_file_title_fts_idx (title)"""
        )

def create_core_team():
    try:
        if "nextgrp" not in frappe.get_installed_apps():
            return

        # Lấy thông tin organization đầu tiên
        organizations = frappe.get_all("Organization", limit=1, order_by="creation asc", fields=["name"])
        if not organizations:
            frappe.log_error("Không tìm thấy tổ chức nào", "create_core_team")
            return {"status": "error", "message": "Không tìm thấy tổ chức nào"}
        
        team_name =  organizations[0].name
        
        # Lấy user đầu tiên
        first_user = frappe.get_all(
            "User", 
            filters={
                "name": ["not in", ["Administrator", "Guest"]],
                "enabled": 1,
                "user_type": "System User"
            },
            fields=["name", "email"],
            order_by="creation asc",
            limit=1
        )
        
        if not first_user:
            frappe.log_error("Không tìm thấy người dùng hợp lệ", "create_core_team")
            return {"status": "error", "message": "No valid user found"}
        
        # Tạo Drive Team với tên organization
        team = frappe.get_doc({
            "doctype": "Drive Team",
            "title": team_name,
            "team_domain": first_user[0].email.split("@")[-1] if first_user else "",
        }).insert(ignore_permissions=True)
        
        # Thêm user đầu tiên làm manager (access_level = 2)
        team.append("users", {
            "user": first_user[0].email, 
            "access_level": 2,
            "is_admin": 1
        })
        team.save(ignore_permissions=True)
        
        return {"status": "success", "team_name": team.name, "manager": first_user[0].email}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_core_team")
        return {"status": "error", "message": str(e)}