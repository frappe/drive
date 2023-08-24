import frappe


@frappe.whitelist()
def get_name_of_all_user_groups():
    try:
        user_groups = frappe.get_all("User Group")
        return {"user_groups": user_groups}
    except Exception as e:
        return {"message": "Failed to fetch user groups.", "error": str(e)}


@frappe.whitelist()
def get_users_in_group(group_name):
    try:
        user_group = frappe.get_doc("User Group", group_name)
        users = [member.user for member in user_group.user_group_members]
        return {"users": users}
    except Exception as e:
        return {"message": "Failed to fetch users in the group.", "error": str(e)}



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
            return {"message": ("User already exists in the group.")}

        # Add the user to the group
        user_group.append("user_group_members", {"user": user_email})
        user_group.save(ignore_permissions=True)

        return {
            "message": ("User added to the group successfully."),
            "user_group": user_group.name,
        }

    except Exception as e:
        return {"message": ("Failed to add user to the group."), "error": str(e)}


@frappe.whitelist()
def add_users_to_group(group_name, user_emails=[]):
    try:
        # Get the User Group document
        user_group = frappe.get_doc("User Group", group_name)

        # Add each user to the group
        added_users = []
        already_existing_users = []

        existing_members = [member.user for member in user_group.user_group_members]

        for user_email in user_emails:
            if user_email not in existing_members:
                user_group.append("user_group_members", {"user": user_email})
                added_users.append(user_email)
            else:
                already_existing_users.append(user_email)

        if already_existing_users:
            return {
                "message": ("Some users are already a part of the User Group"),
                "existing_users": already_existing_users,
            }

        if added_users:
            user_group.save(ignore_permissions=True)
            return {
                "message": ("Users added to the group successfully."),
                "added_users": added_users,
                "user_group": user_group.name,
            }
        else:
            return {
                "message": ("All users are already in the group."),
                "user_group": user_group.name,
            }
    except Exception as e:
        return {"message": ("Failed to add users to the group."), "error": str(e)}


@frappe.whitelist()
def remove_users_from_group(group_name, user_emails=[]):
    try:
        # Get the User Group document
        user_group = frappe.get_doc("User Group", group_name)

        # Remove specified users from the group
        removed_users = []
        existing_members = [member.user for member in user_group.user_group_members]

        for user_email in user_emails:
            if user_email in existing_members:
                user_group.user_group_members = [
                    member
                    for member in user_group.user_group_members
                    if member.user != user_email
                ]
                removed_users.append(user_email)

        if removed_users:
            user_group.save(ignore_permissions=True)
            return {
                "message": ("Users removed from the group successfully."),
                "removed_users": removed_users,
                "user_group": user_group.name,
            }
        else:
            return {
                "message": ("No specified users were found in the group."),
                "user_group": user_group.name,
            }
    except Exception as e:
        return {"message": ("Failed to remove users from the group."), "error": str(e)}
