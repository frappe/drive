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
  it("Defaults to home", () => {
    cy.button("Home").should("have.class", "!bg-surface-selected");
  });
  it("Search popup", () => {
    cy.button("Find").click();
    cy.get("[role=dialog]").should("have.data", "state", "open");

    // Closes on escape
    cy.get("body").type("{esc}");
    cy.get("[role=dialog]").should("not.exist");

    // Opens on shortcut
    cy.get("body").type("{meta}k");
    cy.get("[role=dialog]").should("have.data", "state", "open");
  });
});
