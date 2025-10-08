// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Drive File", {
  refresh: (frm) => {
    frm.add_custom_button(__("Permissions"), function () {
      window.open("/app/drive-permission?entity=" + frm.doc.name);
    });
    frm.add_custom_button(__("Open in Drive"), function () {
      window.open("/drive/g/" + frm.doc.name, "_blank");
    });
  },
});
