import frappe


import frappe


def execute():
    """
    Script migrate để điền dữ liệu vào bảng Drive Trash từ các file đã bị xóa (trash) hiện có
    """
    frappe.reload_doc("drive", "doctype", "drive_trash")
    
    # Lấy tất cả file hiện đang trong thùng rác (is_active = 0)
    trashed_files = frappe.db.sql("""
        SELECT name, title, team, path, owner, modified
        FROM `tabDrive File`
        WHERE is_active = 0
    """, as_dict=True)
    
    # Tạo bản ghi Drive Trash cho mỗi file đã bị xóa
    for file_data in trashed_files:
        # Kiểm tra xem bản ghi trong Trash đã tồn tại chưa
        existing_trash = frappe.db.exists({
            "doctype": "Drive Trash",
            "entity": file_data.name,
            "user": file_data.owner
        })
        
        if not existing_trash:
            try:
                trash_doc = frappe.get_doc({
                    "doctype": "Drive Trash",
                    "entity": file_data.name,
                    "user": file_data.owner,
                    "team": file_data.team,
                    "original_path": file_data.path,
                    "trashed_on": file_data.modified
                })
                trash_doc.insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.logger().error(f"Lỗi khi tạo bản ghi Trash cho {file_data.name}: {e}")
                continue
    
    print(f"Hoàn tất migrate. Đã tạo {len(trashed_files)} bản ghi Drive Trash.")

