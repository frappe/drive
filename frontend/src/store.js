import { createStore } from "vuex"
import { call } from "frappe-ui"
import { clear } from "idb-keyval"

let getCookies = () => {
  return Object.fromEntries(
    document.cookie
      .split("; ")
      .map((cookie) => cookie.split("="))
      .map((entry) => [entry[0], decodeURIComponent(entry[1])])
  )
}
const { user_id, system_user, full_name, user_image } = getCookies()
const getJson = (key, initial) => {
  try {
    return JSON.parse(localStorage.getItem(key)) || initial
  } catch {
    return initial
  }
}
const store = createStore({
  state: {
    user: {
      id: user_id,
      systemUser: system_user === "yes",
      fullName: full_name,
      imageURL: user_image,
    },
    uploads: [],
    connectedUsers: [],
    sortOrder: getJson("sortOrder", {}),
    view: getJson("view", "list"),
    shareView: getJson("shareView", "with"),
    activeTags: [],
    activeEntity: null,
    notifCount: 0,
    pasteData: { entities: [], action: null },
    showInfo: false,
    currentFolder: {
      name: getJson("currentFolder", {}),
      team: getJson("currentFolderTeam", {}),
      entities: getJson("currentEntitites", []),
    },
    breadcrumbs: getJson("breadcrumbs", [{ label: "Home", route: "/" }]),
    // Writer ones
    hasWriteAccess: false,
    allComments: "",
    activeCommentsInstance: "",
    IsSidebarExpanded: JSON.parse(
      localStorage.getItem("IsSidebarExpanded") || true
    ),
    passiveRename: false,
    editorNewTab: localStorage.getItem("editorNewTab")
      ? JSON.parse(localStorage.getItem("editorNewTab"))
      : false,
  },
  getters: {
    isLoggedIn: (state) => {
      return state.user.id && state.user.id !== "Guest"
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
    toggleEditorNewTab(state) {
      state.editorNewTab = !state.editorNewTab
      localStorage.setItem("editorNewTab", JSON.stringify(state.editorNewTab))
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
    setActiveEntity(state, payload) {
      state.activeEntity = payload
    },
    setCurrentFolder(state, payload) {
      // Don't clear cache for performance's sake (state is cleared on every reroute)
      if (payload === null)
        state.currentFolder = { name: null, team: null, entities: [] }
      else {
        state.currentFolder = { ...state.currentFolder, ...payload }
        localStorage.setItem(
          "currentFolder",
          JSON.stringify(state.currentFolder.name)
        )
        localStorage.setItem(
          "currentFolderTeam",
          JSON.stringify(state.currentFolder.team)
        )
        localStorage.setItem(
          "currentEntitites",
          JSON.stringify(state.currentFolder.entities)
        )
      }
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
    setBreadcrumbs(state, payload) {
      localStorage.setItem("breadcrumbs", JSON.stringify(payload))
      state.breadcrumbs = payload
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
    async logout() {
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
