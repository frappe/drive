import { createStore } from "vuex";
import { call } from "frappe-ui";
import { clear } from "idb-keyval";

let getCookies = () => {
  return Object.fromEntries(
    document.cookie
      .split("; ")
      .map((cookie) => cookie.split("="))
      .map((entry) => [entry[0], decodeURIComponent(entry[1])])
  );
};

const store = createStore({
  state: {
    auth: {
      loading: false,
      user_id: getCookies().user_id,
    },
    user: {
      fullName: getCookies().full_name,
      imageURL: getCookies().user_image,
    },
    uploads: [],
    sortOrder: JSON.parse(localStorage.getItem("sortOrder")) || {
      label: "Modified",
      field: "modified",
      ascending: false,
    },
    view: JSON.parse(localStorage.getItem("view")) || "grid",
    entityInfo: null,
    pasteData: { entities: [], action: null },
    showInfo: localStorage.getItem("showInfo") || false,
    hasWriteAccess: false,
    // Default to empty string to upload to user Home folder
    currentFolderID: "",
    homeFolderID: "",
    currentBreadcrumbs: JSON.parse(
      localStorage.getItem("currentBreadcrumbs")
    ) || [{ label: "", route: "" }],
    ctaButton: {
      prefix: "upload",
      suffix: "chevron-down",
      text: "Upload",
      emit: "",
      variant: "solid",
    },
    allComments: "",
    activeCommentsInstance: "",
  },
  getters: {
    isLoggedIn: (state) => {
      return state.auth.user_id && state.auth.user_id !== "Guest";
    },
    uploadsInProgress: (state) => {
      return state.uploads.filter((upload) => !upload.completed);
    },
    uploadsCompleted: (state) => {
      return state.uploads.filter((upload) => upload.completed);
    },
  },
  mutations: {
    setAuth(state, auth) {
      Object.assign(state.auth, auth);
    },
    setUser(state, user) {
      Object.assign(state.user, user);
    },
    setUploads(state, uploads) {
      state.uploads = uploads;
    },
    pushToUploads(state, upload) {
      state.uploads.push(upload);
    },
    updateUpload(state, payload) {
      let index = state.uploads.findIndex(
        (upload) => upload.uuid == payload.uuid
      );
      Object.assign(state.uploads[index], payload);
    },
    setSortOrder(state, payload) {
      localStorage.setItem("sortOrder", JSON.stringify(payload));
      state.sortOrder = payload;
    },
    toggleView(state, payload) {
      localStorage.setItem("view", JSON.stringify(payload));
      state.view = payload;
    },
    setEntityInfo(state, payload) {
      localStorage.setItem("entityInfo", payload);
      state.entityInfo = payload;
    },
    setPasteData(state, payload) {
      state.pasteData = payload;
    },
    setShowInfo(state, payload) {
      localStorage.setItem("showInfo", payload);
      state.showInfo = payload;
    },
    setAllComments(state, payload) {
      /* localStorage.setItem("allDocComments",payload); */
      state.allComments = payload;
    },
    setActiveCommentsInstance(state, payload) {
      state.activeCommentsInstance = payload;
    },
    setHasWriteAccess(state, payload) {
      state.hasWriteAccess = payload;
    },
    setCurrentFolderID(state, payload) {
      state.currentFolderID = payload;
    },
    setHomeFolderID(state, payload) {
      state.homeFolderID = payload;
    },
    setCurrentBreadcrumbs(state, payload) {
      localStorage.setItem("currentBreadcrumbs", JSON.stringify(payload));
      state.currentBreadcrumbs = payload;
    },
    setCtaButton(state, payload) {
      state.ctaButton = payload;
    },
  },
  actions: {
    async login({ commit }, payload) {
      commit("setAuth", { loading: true });
      clear();
      let res = await call("login", {
        usr: payload.email,
        pwd: payload.password,
      });
      if (res) {
        commit("setAuth", {
          loading: false,
          user_id: getCookies().user_id,
        });
        commit("setUser", {
          fullName: getCookies().full_name,
          imageURL: getCookies().user_image
            ? window.location.origin + getCookies().user_image
            : null,
        });
        return res;
      }
      return false;
    },
    async logout({ commit }) {
      commit("setAuth", { loading: true });
      await call("logout");
      clear();
      window.location.reload();
    },
    clearUploads({ commit }) {
      commit("setUploads", []);
    },
  },
});

export default store;
