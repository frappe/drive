import FileUploaderComponent from "./FileUploader.vue";
import FrappeDriveLogo from "./FrappeDriveLogo.vue";
import { createApp } from "vue";

DRIVE_UPLOADER = {
  label: "Drive",
  icon: FrappeDriveLogo,
  action: async ({ dialog, uploader, ...obj }) => {
    dialog.hide();
    const d = new frappe.ui.Dialog({
      title: "Upload from Frappe Drive",
      primary_action_label: "Upload",
      primary_action() {
        file = component.selected_node;
        uploader.upload_file({
          file_url: `/api/method/drive.api.files.get_file_content?entity_name=${file.value}`,
          private: file.share_count === -2 ? 0 : 1,
          file_name: file.label,
          ...obj,
        });
        return d.hide();
      },
    });

    // Fetch all teams first
    const teamsResp = await frappe.call("drive.api.permissions.get_teams");
    const teams = teamsResp.message || [];
    if (!teams.length) {
      return frappe.msgprint(__("No teams available"));
    }
    let app = createApp(FileUploaderComponent);
    const component = app.mount(d.body);
    d.show();
  },
};

(async () => {
  await frappe.require("file_uploader.bundle.js");
  if (frappe.ui.FileUploader?.UploadOptions)
    frappe.ui.FileUploader.UploadOptions.push(DRIVE_UPLOADER);
})();
