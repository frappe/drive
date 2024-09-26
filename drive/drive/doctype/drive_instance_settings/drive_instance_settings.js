// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Drive Instance Settings", {
  onload: function (frm) {
    frm.initialVal = frm.doc.self_storage_limit;
  },
  validate(frm) {
    if (frm.doc.self_storage_limit !== frm.initialVal) {
      if (frm.doc.self_storage_limit) {
        frm.set_value("self_storage_limit", frm.doc.self_storage_limit * 1024);
      }
      frm.initialVal = frm.doc.self_storage_limit;
    }
  },
});
