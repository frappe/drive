describe("Core functionality", () => {
  before(() => {
    cy.request({
      method: "POST",
      url: "/api/method/drive.test_api.clear_data",
    });
  });
  beforeEach(() => {
    cy.login();
    cy.visit("/drive");
  });
  // it("Dropzone", () => {
  //   cy.wait(1000);
  //   cy.fixture("files/truth.txt", "base64").then((fileContent) => {
  //     cy.get("#dropzone").attachFile(
  //       {
  //         fileContent,
  //         fileName: "truth.txt",
  //         mimeType: "application/pdf",
  //         encoding: "base64",
  //       },
  //       { subjectType: "drag-n-drop" }
  //     );
  //   });
  //   cy.wait(1000);
  //   cy.get("#drop-area").within(() => {
  //     cy.contains("truth").should("exist").click();
  //   });

  //   cy.get("#navbar").within(() => {
  //     cy.contains("truth.txt");
  //     cy.link("Home").should("have.attr", "href", "/drive/");

  //     // Go back home
  //     cy.link("Home").click();
  //     cy.location("pathname").should("eq", "/drive/");
  //   });

  //   // Upload larger file and check if limits change
  //   cy.contains("0.1 KB used out of 5 GB");
  //   cy.fixture("files/domination.pdf", "base64").then((fileContent) => {
  //     cy.get("#dropzone").attachFile(
  //       {
  //         fileContent,
  //         fileName: "domination.pdf",
  //         mimeType: "application/pdf",
  //         encoding: "base64",
  //       },
  //       { subjectType: "drag-n-drop" }
  //     );
  //   });
  //   cy.contains("489.7 KB used out of 5 GB");
  // });

  // it("Recents", () => {
  //   cy.button("Recents").click();
  //   cy.get("#drop-area").within(() => {
  //     cy.contains("truth").should("exist");
  //   });
  //   cy.button("Clear").click();
  //   cy.dialog().within(() => {
  //     cy.button("Clear").click();
  //   });
  //   cy.contains("No recent files.");
  // });

  it("Teams", () => {
    cy.wait(1500);
    cy.get("body").type("{meta},");

    // Basic team page
    cy.button("Teams").click();
    cy.contains("No teams yet.").should("exist");
    // Add team
    cy.dialog().within(() => cy.get(".lucide-plus").click());
    cy.focused().type("Family");
    cy.button("Add").click();
    cy.wait(400);

    // Team is updated immediately
    cy.dialog().within(() => {
      cy.contains("Four McTest")
        .parents("div.flex.items-center.justify-start")
        .within(() => {
          cy.contains("Manager (you)").should("exist");
        });
    });
    cy.location("pathname").should("include", "/drive/t/");
    cy.get("body").type("{esc}");
    cy.get("#navbar").within(() => {
      cy.contains("Family").should("exist");
    });
    cy.button("Family").should("have.class", "!bg-surface-selected");

    cy.fixture("files/pfp.jpg", "base64").then((fileContent) => {
      cy.list().attachFile(
        {
          fileContent,
          fileName: "pfp.jpg",
          mimeType: "image/jpeg",
          encoding: "base64",
        },
        { subjectType: "drag-n-drop" }
      );
    });
  });

  it("Folders", () => {
    cy.get("body").get(".lucide-plus").click();
    cy.button(/^Folder$/).click();
    let folder = "A Folder of Wonders";
    cy.focused().type(folder + "{enter}");
    cy.list().within(() => cy.get(folder).should("exist"));
  });
});
