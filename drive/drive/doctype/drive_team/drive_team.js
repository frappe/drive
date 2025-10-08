// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Drive Team", {
  refresh: function (frm) {
    frm.add_custom_button(__("Open in Drive"), function () {
      window.open("/drive/t/" + frm.doc.name, "_blank");
    });
  },
});
