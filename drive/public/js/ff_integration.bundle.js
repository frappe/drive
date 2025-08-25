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
          file_url:
            "/api/method/drive.api.files.get_file_content?entity_name=" +
            file.value,
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
    return;

    // Helper to build tree HTML
    function buildTree(folders, parent = "") {
      const children = folders.filter((f) => f.parent === parent);
      if (!children.length) return "";
      return `<ul style="margin-left:1em;">${children
        .map(
          (f) =>
            `<li data-value="${f.value}">
                <span>${f.label}</span>
                ${buildTree(folders, f.value)}
              </li>`
        )
        .join("")}</ul>`;
    }

    // Content HTML with team selector
    const content = `
        <div style="min-width:500px;">
          <div style="margin-bottom:1em;">
            <label><strong>Select Team:</strong></label>
            <select id="team-select" style="width:100%;padding:0.3em;">
              ${teams
                .map(
                  (t) =>
                    `<option value="${t.name}">${t.label || t.name}</option>`
                )
                .join("")}
            </select>
          </div>
          <div style="display:flex;gap:1em;">
            <div style="flex:1;">
              <h4>Home Files</h4>
              <input type="text" id="home-search" placeholder="Search Home folders..." style="width:100%;margin-bottom:0.5em;" />
              <div id="home-tree"></div>
            </div>
            <div style="flex:1;">
              <h4>Team Files</h4>
              <input type="text" id="team-search" placeholder="Search Team folders..." style="width:100%;margin-bottom:0.5em;" />
              <div id="team-tree"></div>
            </div>
          </div>
        </div>
      `;

    // const d = new frappe.ui.Dialog({
    //   title: "Select Drive Folder",
    //   fields: [{ fieldtype: "HTML", options: content }],
    //   primary_action_label: "Select",
    //   primary_action(values) {
    //     // Add logic here to get selected folder
    //     d.hide();
    //   },
    // });

    // d.show();

    // Function to load folders for selected team
    async function loadFoldersForTeam(team) {
      const [homeFolders, teamFolders] = await Promise.all([
        frappe.call("drive.api.list.files", {
          folders: 1,
          personal: 1,
          team,
        }),
        frappe.call("drive.api.list.files", {
          folders: 1,
          personal: 0,
          team,
        }),
      ]);

      document.getElementById("home-tree").innerHTML = buildTree(
        homeFolders.message
      );
      document.getElementById("team-tree").innerHTML = buildTree(
        teamFolders.message
      );
    }

    // Init with first team
    const initialTeam = teams[0].name;
    await loadFoldersForTeam(initialTeam);

    // Listen for team changes
    document
      .getElementById("team-select")
      .addEventListener("change", async function (e) {
        await loadFoldersForTeam(e.target.value);
      });

    // Search filters
    setTimeout(() => {
      document
        .getElementById("home-search")
        .addEventListener("input", function (e) {
          const val = e.target.value.toLowerCase();
          document.querySelectorAll("#home-tree li").forEach((li) => {
            li.style.display = li.innerText.toLowerCase().includes(val)
              ? ""
              : "none";
          });
        });
      document
        .getElementById("team-search")
        .addEventListener("input", function (e) {
          const val = e.target.value.toLowerCase();
          document.querySelectorAll("#team-tree li").forEach((li) => {
            li.style.display = li.innerText.toLowerCase().includes(val)
              ? ""
              : "none";
          });
        });
    }, 300);
  },
};

(async () => {
  await frappe.require("file_uploader.bundle.js");
  frappe.ui.FileUploader.UploadOptions.push(DRIVE_UPLOADER);
})();
