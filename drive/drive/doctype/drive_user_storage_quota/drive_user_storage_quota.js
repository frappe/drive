// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Drive User Storage Quota", {
  onload: function (frm) {
    frm.initialVal = frm.doc.user_storage_limit;
  },
  validate(frm) {
    if (frm.doc.user_storage_limit !== frm.initialVal) {
      if (frm.doc.user_storage_limit) {
        frm.set_value("user_storage_limit", frm.doc.user_storage_limit * 1024);
      }
      frm.initialVal = frm.doc.user_storage_limit;
    }
  },
});
