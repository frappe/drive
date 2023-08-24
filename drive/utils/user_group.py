import frappe

@frappe.whitelist()
def create_user_group(group_name, members=[]):
    try:
        # Create a new User Group
        new_group = frappe.get_doc({
            "doctype": "User Group",
            "name": group_name,
            "user_group_members": [{"user": member} for member in members]
        })
        
        new_group.insert(ignore_permissions=True)

        return {
            "message":("User Group created successfully."),
            "user_group": new_group.name
        }
    
    except Exception as e:
        frappe.log_error(title="User Group Creation Failed", message=str(e))
        return {
            "message": ("User Group creation failed."),
            "error": str(e)
        }
