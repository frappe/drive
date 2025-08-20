import frappe
from frappe.utils import cint


@frappe.whitelist()
def add_user_to_drive_team(doc, method):
    if doc.user_type != "System User" or not cint(doc.enabled):
        return
    
    try:
        if "nextgrp" not in frappe.get_installed_apps():
            return
            
        organization_name = _get_organization_name()
        if not organization_name:
            frappe.log_error(
                message="Không tìm thấy tổ chức nào trong hệ thống", 
                title="No Organization"
            )
            return
        
        team = _get_or_create_drive_team(organization_name)
        if not team:
            frappe.log_error(
                message=f"Không thể tạo hoặc tìm thấy Drive Team cho tổ chức: {organization_name}",
                title="Drive Team Hook - Tạo nhóm không thành công"
            )
            return
        
        _add_user_to_team(team, doc.name)
        _create_drive_settings(doc.name, team.name)
        
        frappe.logger().info(f"Đã thêm user {doc.name} vào Drive Team {team.name} và tạo Drive Settings thành công")
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Drive Team Hook Error - User: {doc.name}"
        )


def _get_organization_name():
    cache_key = "drive_team_organization_name"
    organization_name = frappe.cache().get_value(cache_key)
    
    if not organization_name:
        organizations = frappe.get_all(
            "Organization", 
            limit=1, 
            order_by="creation asc", 
            fields=["name"],
            pluck="name"
        )
        
        if organizations:
            organization_name = organizations[0]
            frappe.cache().set_value(cache_key, organization_name, expires_in_sec=3600)
    
    return organization_name


def _get_or_create_drive_team(team_name):
    try:
        team = frappe.get_doc("Drive Team", {"title": team_name})
        return team
    except frappe.DoesNotExistError:
        try:
            team = frappe.get_doc({
                "doctype": "Drive Team",
                "title": team_name,
                "team_domain": "",
            })
            team.insert(ignore_permissions=True)
            return team
        except Exception as e:
            frappe.log_error(
                message=f"Lỗi khi tạo Drive Team: {frappe.get_traceback()}",
                title="Drive Team Creation Error"
            )
            return None


def _add_user_to_team(team, user_email):
    if not team.team_domain and "@" in user_email:
        team.team_domain = user_email.split("@")[-1]
    
    team.append("users", {
        "user": user_email,
        "access_level": 1
    })
    
    team.save(ignore_permissions=True)


def _create_drive_settings(user_email, default_team):
    """
    Tạo Drive Settings cho user với team mặc định.
    """
    try:
        # Kiểm tra xem Drive Settings đã tồn tại chưa
        if frappe.db.exists("Drive Settings", {"user": user_email}):
            frappe.logger().info(f"Drive Settings cho user {user_email} đã tồn tại")
            return
        
        # Tạo Drive Settings mới
        drive_settings = frappe.get_doc({
            "doctype": "Drive Settings",
            "user": user_email,
            "default_team": default_team,
            "single_click": 1,
            "auto_detect_links": 0 
        })
        
        drive_settings.insert(ignore_permissions=True)
        frappe.logger().info(f"Đã tạo Drive Settings cho user {user_email} với default team {default_team}")
        
    except Exception as e:
        frappe.log_error(
            message=f"Lỗi khi tạo Drive Settings cho user {user_email}: {frappe.get_traceback()}",
            title="Drive Settings Creation Error"
        )