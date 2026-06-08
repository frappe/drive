
frappe.ui.form.on('File', {
  refresh: (frm) => {
    if (frm.doc.team) {
      frm.add_custom_button(__('Permissions'), function () {
        window.open('/app/drive-permission?entity=' + frm.doc.name)
      })
      frm.add_custom_button(__('Open in Drive'), function () {
        window.open('/drive/g/' + frm.doc.name, '_blank')
      })
    }
  },
})
