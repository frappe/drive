import frappe


@frappe.whitelist()
def create_user_group(group_name, members=[]):
    try:
        # Create a new User Group
        new_group = frappe.get_doc(
            {
                "doctype": "User Group",
                "name": group_name,
                "user_group_members": [{"user": member} for member in members],
            }
        )

        new_group.insert(ignore_permissions=True)

        return {
            "message": ("User Group created successfully."),
            "user_group": new_group.name,
        }

    except Exception as e:
        return {"message": ("User Group creation failed."), "error": str(e)}


@frappe.whitelist()
def add_user_to_group(group_name, user_email):
    try:
        # Get the User Group document
        user_group = frappe.get_doc("User Group", group_name)

        # Check if the user is already in the group
        existing_members = [member.user for member in user_group.user_group_members]
        if user_email in existing_members:
            return {
                "message": ("User already exists in the group.")
            }
        
        # Add the user to the group
        user_group.append("user_group_members", {"user": user_email})
        user_group.save(ignore_permissions=True)

        return {
            "message": ("User added to the group successfully."),
            "user_group": user_group.name
        }
    except Exception as e:
        return {
            "message": ("Failed to add user to the group."),
            "error": str(e)
        }