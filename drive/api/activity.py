import frappe
from pypika import Query, Order, Table


def create_new_activity_log(
    doctype,
    document_name,
    activity_type,
    activity_message,
    document_field=None,
    field_old_value=None,
    field_new_value=None,
):
    doc = frappe.new_doc("Drive Entity Activity Log")
    doc.document_type = doctype
    doc.document_name = document_name
    doc.document_field = document_field
    doc.action_type = activity_type
    doc.message = activity_message
    doc.owner = frappe.session.user
    if document_field:
        doc.old_value = field_old_value
        doc.new_value = field_new_value
    doc.save()
    return


@frappe.whitelist()
def get_entity_activity_log(entity_name):
    """
    Warning: Assumes `Drive Entity` only
    """
    Activity = frappe.qb.DocType("Drive Entity Activity Log")
    User = frappe.qb.DocType("User")
    Docshare = frappe.qb.DocType("Drive Docshare")
    selectedFields = [
        Activity.name,
        Activity.document_type,
        Activity.message,
        Activity.owner,
        Activity.action_type,
        Activity.old_value,
        Activity.new_value,
        Activity.creation,
        User.full_name,
        User.user_image,
        Docshare.public.as_("general_share"),
        Docshare.everyone.as_("general_share"),
        Docshare.user_doctype.as_("share_user_type"),
        Docshare.user_name.as_("share_user_name"),
    ]
    query = (
        frappe.qb.from_(Activity)
        .select(*selectedFields)
        .left_join(User)
        .on(Activity.owner == User.email)
        .left_join(Docshare)
        .on((Activity.document_name == Docshare.name))
        .where(
            ((Activity.document_type == "Drive DocShare") & (Docshare.share_name == entity_name))
            | (
                (Activity.document_type == "Drive Entity")
                & (Activity.document_name == entity_name)
            )
        )
        .orderby(Activity.creation, order=Order.desc)
    )

    result = query.run(as_dict=True)
    for i in result:
        if i.document_type == "Drive DocShare" and i.share_user_type == "User":
            i.share_user_fullname, i.share_user_image = frappe.get_value(
                "User", i.share_user_name, ["full_name", "user_image"]
            )

    return result
