import { createStore } from "vuex"
import { call } from "frappe-ui"
import { clear } from "idb-keyval"
import { get, set } from "idb-keyval"

let getCookies = () => {
  return Object.fromEntries(
    document.cookie
      .split("; ")
      .map((cookie) => cookie.split("="))
      .map((entry) => [entry[0], decodeURIComponent(entry[1])])
  )
}

const store = createStore({
  state: {
    auth: {
      loading: false,
      user_id: getCookies().user_id,
    },
    user: {
      systemUser: getCookies().system_user === "yes",
      fullName: getCookies().full_name,
      imageURL: getCookies().user_image,
      driveAdmin: false,
    },
    error: {
      iconName: "x-circle",
      iconClass: "fill-red-500 stroke-white",
      primaryMessage: "404 Not Found",
      secondaryMessage: "The resource you're looking for does not exist",
    },
    uploads: [],
    connectedUsers: [],
    sortOrder: JSON.parse(localStorage.getItem("sortOrder")) || {
      label: "Modified",
      field: "modified",
      ascending: false,
    },
    view: JSON.parse(localStorage.getItem("view")) || "grid",
    shareView: JSON.parse(localStorage.getItem("shareView")) || "with",
    activeFilters: [],
    notifCount: 0,
    entityInfo:
      JSON.parse(localStorage.getItem("selectedEntities")) ||
      JSON.parse(localStorage.getItem("currentFolder")) ||
      [],
    currentFolder: JSON.parse(localStorage.getItem("currentFolder")) || [],
    currentViewEntites: get("currentViewEntites") || [],
    pasteData: { entities: [], action: null },
    showInfo: JSON.parse(localStorage.getItem("showInfo")) || false,
    hasWriteAccess: false,
    // Default to empty string to upload to user Home folder
    currentFolderID: "",
    homeFolderID: localStorage.getItem("homeFolderID"),
    currentBreadcrumbs: JSON.parse(
      localStorage.getItem("currentBreadcrumbs")
    ) || [{ label: "Home", route: "/home" }],
    allComments: "",
    activeCommentsInstance: "",
    IsSidebarExpanded: JSON.parse(
      localStorage.getItem("IsSidebarExpanded") || true
    ),
    passiveRename: false,
  },
  getters: {
    isLoggedIn: (state) => {
      return state.auth.user_id && state.auth.user_id !== "Guest"
    },
    uploadsInProgress: (state) => {
      return state.uploads.filter((upload) => !upload.completed)
    },
    uploadsCompleted: (state) => {
      return state.uploads.filter((upload) => upload.completed)
    },
  },
  mutations: {
    setAuth(state, auth) {
      Object.assign(state.auth, auth)
    },
    setError(state, error) {
      Object.assign(state.error, error)
    },
    setUser(state, user) {
      Object.assign(state.user, user)
    },
    setUploads(state, uploads) {
      state.uploads = uploads
    },
    setConnectedUsers(state, connectedUsers) {
      state.connectedUsers = connectedUsers
    },
    pushToUploads(state, upload) {
      state.uploads.push(upload)
    },
    updateUpload(state, payload) {
      let index = state.uploads.findIndex(
        (upload) => upload.uuid == payload.uuid
      )
      Object.assign(state.uploads[index], payload)
    },
    setSortOrder(state, payload) {
      localStorage.setItem("sortOrder", JSON.stringify(payload))
      state.sortOrder = payload
    },
    toggleView(state, payload) {
      localStorage.setItem("view", JSON.stringify(payload))
      state.view = payload
    },
    toggleShareView(state, payload) {
      localStorage.setItem("shareView", JSON.stringify(payload))
      state.shareView = payload
    },
    setEntityInfo(state, payload) {
      localStorage.setItem("selectedEntities", JSON.stringify(payload))
      state.entityInfo = payload
    },
    setCurrentFolder(state, payload) {
      localStorage.setItem("currentFolder", JSON.stringify(payload))
      state.currentFolder = payload
    },
    setCurrentViewEntites(state, payload) {
      state.currentViewEntites = payload
      set("currentViewEntites", JSON.stringify(payload))
    },
    setPasteData(state, payload) {
      state.pasteData = payload
    },
    setShowInfo(state, payload) {
      localStorage.setItem("showInfo", payload)
      state.showInfo = payload
    },
    setAllComments(state, payload) {
      /* localStorage.setItem("allDocComments",payload); */
      state.allComments = payload
    },
    setActiveCommentsInstance(state, payload) {
      state.activeCommentsInstance = payload
    },
    setHasWriteAccess(state, payload) {
      state.hasWriteAccess = payload
    },
    setCurrentFolderID(state, payload) {
      state.currentFolderID = payload
    },
    setHomeFolderID(state, payload) {
      state.homeFolderID = payload
      localStorage.setItem("homeFolderID", payload)
    },
    setCurrentBreadcrumbs(state, payload) {
      localStorage.setItem("currentBreadcrumbs", JSON.stringify(payload))
      state.currentBreadcrumbs = payload
    },
    setIsSidebarExpanded(state, payload) {
      localStorage.setItem("IsSidebarExpanded", JSON.stringify(payload))
      state.IsSidebarExpanded = payload
    },
  },
  actions: {
    async login({ commit }, payload) {
      localStorage.removeItem("is_drive_admin")
      commit("setAuth", { loading: true })
      clear()
      let res = await call("login", {
        usr: payload.email,
        pwd: payload.password,
      })
      if (res) {
        commit("setAuth", {
          loading: false,
          user_id: getCookies().user_id,
        })
        commit("setUser", {
          fullName: getCookies().full_name,
          imageURL: getCookies().user_image
            ? window.location.origin + getCookies().user_image
            : null,
        })
        return res
      }
    },
    async logout({ commit }) {
      commit("setAuth", { loading: true })
      await call("logout")
      clear()
      window.location.reload()
    },
    clearUploads({ commit }) {
      commit("setUploads", [])
    },
  },
})

export default store
