# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from raven.raven_bot.doctype.raven_bot.raven_bot import RavenBot
import json


class DriveNotification(Document):
    def after_insert(self):
        bot_docs = frappe.conf.get("bot_docs")
        if not bot_docs:
            return
        full_name = (
            frappe.db.get_value("User", {"name": self.from_user}, "full_name") or self.from_user
        )
        if self.type == "Share":
            message_data = {
                "key": "share_document",
                "title": f"{full_name} đã chia sẻ với bạn tài liệu:",
                "full_name_owner": full_name,
                "to_user": self.to_user,
                "type": self.type,
                "entity_type": self.entity_type,
                "message": self.message,
                "file_name": self.file_name,
                "link": f"/drive/t/{self.id_team}/file/{self.notif_doctype_name}",
            }
            RavenBot.send_notification_to_user(
                bot_name=bot_docs,
                user_id=self.to_user,
                message=json.dumps(message_data, ensure_ascii=False, default=str),
            )

        if self.type == "Mention":
            comment_doc = frappe.get_doc("Comment", self.comment_id)
            message_data = {
                "key": "mention_document",
                "title": f"{full_name} đã nhắc đến bạn trong",
                "full_name_owner": full_name,
                "to_user": self.to_user,
                "type": self.type,
                "entity_type": self.entity_type,
                "message": self.message,
                "file_name": self.file_name,
                "comment_id": comment_doc.name or "",
                "comment_content": comment_doc.content or "",
                "link": f"/drive/t/{self.id_team}/file/{self.notif_doctype_name}",
            }
            RavenBot.send_notification_to_user(
                bot_name=bot_docs,
                user_id=self.to_user,
                message=json.dumps(message_data, ensure_ascii=False, default=str),
            )
