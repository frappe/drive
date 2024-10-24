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
      role: false,
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
      label: "Name",
      field: "title",
      ascending: true,
    },
    view: JSON.parse(localStorage.getItem("view")) || "grid",
    shareView: JSON.parse(localStorage.getItem("shareView")) || "with",
    elementExists: false,
    activeFilters: [],
    activeTags: [],
    notifCount: 0,
    entityInfo:
      JSON.parse(localStorage.getItem("selectedEntities")) ||
      JSON.parse(localStorage.getItem("currentFolder")) ||
      [],
    serverTZ: null,
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
    foldersBefore: localStorage.getItem("foldersBefore")
      ? JSON.parse(localStorage.getItem("foldersBefore"))
      : true,
    singleClick: localStorage.getItem("singleClick")
      ? JSON.parse(localStorage.getItem("singleClick"))
      : false,
    editorNewTab: localStorage.getItem("editorNewTab")
      ? JSON.parse(localStorage.getItem("editorNewTab"))
      : false,
  },
  getters: {
    isLoggedIn: (state) => {
      return (
        state.auth.user_id &&
        state.auth.user_id !== "Guest" &&
        state.user.role !== "Guest"
      )
    },
    uploadsInProgress: (state) => {
      return state.uploads.filter((upload) => !upload.completed)
    },
    uploadsFailed: (state) => {
      return state.uploads.filter((upload) => upload.error)
    },
    uploadsCompleted: (state) => {
      return state.uploads.filter((upload) => upload.completed && !upload.error)
    },
  },
  mutations: {
    setElementExists(state, val) {
      state.elementExists = val
    },
    toggleFoldersBefore(state) {
      state.foldersBefore = !state.foldersBefore
      localStorage.setItem("foldersBefore", JSON.stringify(state.foldersBefore))
    },
    toggleSingleClick(state) {
      state.singleClick = !state.singleClick
      localStorage.setItem("singleClick", JSON.stringify(state.singleClick))
    },
    toggleEditorNewTab(state) {
      state.editorNewTab = !state.editorNewTab
      localStorage.setItem("editorNewTab", JSON.stringify(state.editorNewTab))
    },
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
    checkElementPresence({ commit }) {
      const exists = document.getElementById("headlessui-portal-root") !== null
      commit("setElementExists", exists)
    },
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

const observer = new MutationObserver(() => {
  store.dispatch("checkElementPresence")
})
observer.observe(document.body, { childList: true, subtree: true })
export function stopObserving() {
  observer.disconnect()
}

export default store
