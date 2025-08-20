import frappe

def execute():
    """
    Patch để tạo core team cho các site đã tồn tại.
    Team sẽ được đặt tên theo tên Organization và thêm tất cả user vào team.
    User đầu tiên sẽ làm manager, các user còn lại làm member.
    """
    try:
        # Kiểm tra nếu không có nextgrp app thì bỏ qua
        if "nextgrp" not in frappe.get_installed_apps():
            print("Không tìm thấy ứng dụng NextGRP, bỏ qua bước tạo drive team")
            return

        organizations = frappe.get_all("Organization", limit=1)
        if not organizations:
            print("Không tìm thấy tổ chức nào, không thể tạo drive team")
            return
        
        team_name = organizations[0].name

        # Kiểm tra xem đã có Drive Team chưa
        existing_teams = frappe.get_all("Drive Team", filters={"title": team_name})
        if existing_teams:
            # Nếu đã có team, thêm user vào team đầu tiên
            team = frappe.get_doc("Drive Team", existing_teams[0].name)
        else:
            # Tạo Drive Team với tên organization
            team = frappe.get_doc({
                "doctype": "Drive Team",
                "title": team_name,
                "team_domain": "",
            })
            team.insert(ignore_permissions=True)
        
        # Lấy tất cả user hợp lệ (trừ Administrator và Guest)
        all_users = frappe.get_all(
            "User", 
            filters={
                "name": ["not in", ["Administrator", "Guest"]],
                "enabled": 1,
                "user_type": "System User"
            },
            fields=["name", "email"],
            order_by="creation asc"
        )
        
        if not all_users:
            return
        
        # Lấy danh sách user hiện tại trong team
        current_users = [user.user for user in team.users]
        
        # Cập nhật team domain từ user đầu tiên nếu chưa có
        if not team.team_domain and all_users:
            team.team_domain = all_users[0].email.split("@")[-1]
        
        # Thêm tất cả users vào team
        added_count = 0
        for i, user in enumerate(all_users):
            if user.email not in current_users:
                if i == 0 and not current_users:
                    # User đầu tiên làm manager (access_level = 2) nếu team chưa có ai
                    team.append("users", {
                        "user": user.email, 
                        "access_level": 2,
                        "is_admin": 1
                    })
                else:
                    # Các user còn lại làm member (access_level = 1)
                    team.append("users", {
                        "user": user.email, 
                        "access_level": 1,
                        "is_admin": 0
                    })
                added_count += 1
            else:
                print(f"User {user.email} đã tồn tại trong team")
        
        if added_count > 0:
            team.save(ignore_permissions=True)
        else:
            print("Không có người dùng mới nào để thêm")
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_core_team_patch")
