describe("Core functionality", () => {
  before(() => {
    cy.request({
      method: "POST",
      url: "/api/method/drive.test_api.clear_data",
    });
    cy.login();
  });
  beforeEach(() => {
    cy.visit("/drive");
  });
  it("Dropzone", () => {
    cy.wait(1000);
    cy.fixture("files/truth.txt", "base64").then((fileContent) => {
      cy.get("#dropzone").attachFile(
        {
          fileContent,
          fileName: "truth.txt",
          mimeType: "application/pdf",
          encoding: "base64",
        },
        { subjectType: "drag-n-drop" }
      );
    });
    cy.wait(1000);
    cy.get("#drop-area").within(() => {
      cy.contains("truth").should("exist").click();
    });
    cy.wait(1000);
    cy.get("#navbar").within(() => {
      cy.contains("truth.txt");
      cy.link("Home").should("have.attr", "href", "/drive/");
    });
  });
});
