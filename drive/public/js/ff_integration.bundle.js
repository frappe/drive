import FileUploaderComponent from "./FileUploader.vue";
import { createApp } from "vue";

frappe.ui.FileUploaderOthers = [
  {
    label: "Drive",
    icon: '<svg viewBox="0 0 87.3 78" xmlns="http://www.w3.org/2000/svg"><path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" fill="#0066da"/><path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0 -1.2 4.5h27.5z" fill="#00ac47"/><path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" fill="#ea4335"/><path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" fill="#00832d"/><path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684fc"/><path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00"/></svg>',
    action: async (dialog) => {
      dialog.hide();
      const d = new frappe.ui.Dialog({
        title: "Select Drive Folder",

        primary_action_label: "Select",
        primary_action(values) {
          // Add logic here to get selected folder
          d.hide();
        },
      });
      // Fetch all teams first
      const teamsResp = await frappe.call("drive.api.permissions.get_teams");
      const teams = teamsResp.message || [];
      if (!teams.length) {
        return frappe.msgprint(__("No teams available"));
      }
      let app = createApp(FileUploaderComponent);
      // SetVueGlobals(app);
      app.mount(d.body);
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

      const d = new frappe.ui.Dialog({
        title: "Select Drive Folder",
        fields: [{ fieldtype: "HTML", options: content }],
        primary_action_label: "Select",
        primary_action(values) {
          // Add logic here to get selected folder
          d.hide();
        },
      });

      d.show();

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
  },
];
