import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "drive-test",
  testUser: "four@test.io",
  testPassword: "testPassword",
  defaultCommandTimeout: 2000,
  pageLoadTimeout: 15000,
  video: true,
  videoUploadOnPasses: false,
  e2e: {
    baseUrl: "http://localhost:8081",
  },
});
