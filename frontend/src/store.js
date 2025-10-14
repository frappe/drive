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
    sortOrder: getJson("sortOrder", {}),
    view: getJson("view", "list"),
    shareView: getJson("shareView", "with"),
    activeTags: [],
    activeEntity: null,
    currentResource: [],
    listResource: [],
    notifCount: 0,
    pasteData: { entities: [], action: null },
    currentFolder: {
      name: getJson("currentFolder", ""),
      team: getJson("currentFolderTeam", ""),
      entities: getJson("currentEntitites", []),
    },
    breadcrumbs: getJson("breadcrumbs", [{ label: "Home", route: "/" }]),
    sidebarCollapsed: getJson("sidebarCollapsed", false),
    watermarkText: getJson("watermarkText",""),
  },
  getters: {
    isLoggedIn: (state) => {
      return state.user.id && state.user.id !== "Guest"
    },
    uploadsInProgress: (state) =>
      state.uploads.filter((u) => !u.completed && !u.completed),
    uploadsCompleted: (state) =>
      state.uploads.filter((u) => u.completed && !u.error),
    uploadsFailed: (state) => state.uploads.filter((u) => u.error),
  },
  mutations: {
    addUpload(state, payload) {
      state.uploads.push(payload)
    },
    updateUpload(state, payload) {
      const idx = state.uploads.findIndex((u) => u.uuid === payload.uuid)
      if (idx > -1) {
        state.uploads[idx] = { ...state.uploads[idx], ...payload }
      }
    },
    clearUploads(state) {
      state.uploads = []
    },
    removeUpload(state, uuid) {
      state.uploads = state.uploads.filter((u) => u.uuid !== uuid)
    },
    setSortOrder(state, [entity, value]) {
      if (!state.sortOrder) {
        state.sortOrder = {}
      }
      state.sortOrder[entity] = value
      localStorage.setItem("sortOrder", JSON.stringify(state.sortOrder))
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
    setCurrentResource(state, payload) {
      state.currentResource = payload
    },
    setListResource(state, payload) {
      state.listResource = payload
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
    setBreadcrumbs(state, payload) {
      localStorage.setItem("breadcrumbs", JSON.stringify(payload))
      state.breadcrumbs = payload
    },
    setSidebarCollapsed(state, payload) {
      localStorage.setItem("sidebarCollapsed", JSON.stringify(payload))
      state.sidebarCollapsed = payload
    },
    setWatermark(state, payload) {
    state.watermarkText = payload
    localStorage.setItem("watermarkText", JSON.stringify(payload))
  },
  },
  actions: {
    async logout() {
      await call("logout")
      clear()
      window.location.reload()
    },
  },
})

export default store
