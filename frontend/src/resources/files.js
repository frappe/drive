import { createResource } from "frappe-ui"
import { toast } from "@/utils/toasts"

import store from "@/store"
import router from "@/router"
import { prettyData } from "../utils/files"

// GETTERS
const COMMON_OPTIONS = {
  method: "GET",
  debounce: 500,
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      store.commit("setError", {
        primaryMessage: "Forbidden",
        secondaryMessage: "Insufficient permissions for this resource",
      })
      router.replace({ name: "Error" })
    }
  },
  transform(data) {
    store.commit("setCurrentEntitites", data)
    return prettyData(data)
  },
}
export const getHome = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "home-folder-contents",
})

// BROKEN - this is never called (hence, refreshed)
export const getTeams = createResource({
  url: "/api/method/drive.api.permissions.get_teams",
  params: {
    details: 1,
  },
  method: "GET",
  cache: "teams",
})

// Separate for cache purposes
export const getFolderContents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return {
      ...getFolderContents.params,
      ...params,
    }
  },
})

export const getRecents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "recent-folder-contents",
  makeParams: (params) => {
    return { ...params, recents_only: true }
  },
})

export const getPersonal = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "personal-folder-contents",
  makeParams: (params) => {
    return { ...params, personal: 1 }
  },
})

export const getFavourites = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "favourite-folder-contents",
  makeParams: (params) => {
    return { ...params, favourites_only: true }
  },
})

export const getShared = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.shared",
  cache: "shared-folder-contents",
  makeParams: (params) => {
    return { ...params }
  },
})

export const getTrash = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "trash-folder-contents",
  makeParams: (params) => {
    return { ...params, is_active: false }
  },
})

// SETTERS
export const toggleFav = createResource({
  url: "drive.api.files.set_favourite",
  makeParams(data) {
    if (!data) return { clear_all: true }
    const entity_names = data.entities.map(({ name }) => name)
    if (data.entities[0].is_favourite)
      getFavourites.setData((data) =>
        data.filter((n) => !entity_names.includes(n))
      )
    else
      getFavourites.setData((data) =>
        data.filter((n) => entity_names.includes(n))
      )
    return {
      entities: data.entities,
    }
  },
  onSuccess() {
    if (!toggleFav.params.entities) toast("All favourites cleared")
    if (toggleFav.params.entities.length === 1) return
    if (toggleFav.params.entities[0].is_favourite === false)
      toast(`${toggleFav.params.entities.length} items unfavourited`)
    else toast(`${toggleFav.params.entities.length} items favourited`)
  },
})

export const clearRecent = createResource({
  url: "drive.api.files.remove_recents",
  makeParams: (data) =>
    data
      ? {
          entity_names: data.entities.map((e) => e.name),
        }
      : { clear_all: true },
  onSuccess: () =>
    getRecents.previousData > 1
      ? toast(`Cleared  ${getRecents.previousData.length} files from Recents`)
      : null,
})

export const clearTrash = createResource({
  url: "drive.api.files.delete_entities",
  makeParams: (data) =>
    data
      ? {
          entity_names: data.entities.map((e) => e.name),
        }
      : { clear_all: true },
  onSuccess: () =>
    toast(
      `Permanently deleted  ${clearRecent.params.entities} file${
        clearRecent.params.entities === 1 ? "" : "s"
      }.`
    ),
})

export const rename = createResource({
  url: "drive.api.files.call_controller_method",
  method: "POST",
  makeParams: (data) => {
    return {
      method: "rename",
      ...data,
    }
  },
  onSuccess(data) {
    toast({
      title: `Renamed ${store.state.activeEntity.title} to ${rename.params.new_title}`,
      position: "bottom-right",
      timeout: 2,
    })
    store.state.activeEntity.title = data.title
    store.state.passiveRename = false
  },
})

export const createDocument = createResource({
  method: "POST",
  url: "drive.api.files.create_document_entity",
  makeParams: (params) => params,
})

export const togglePersonal = createResource({
  method: "POST",
  url: "drive.api.files.call_controller_method",
  makeParams: (params) => ({ ...params, method: "toggle_personal" }),
  onSuccess: (e) => {
    let index = getPersonal.data.findIndex((k) => k.name === e)
    getHome.data.push(getPersonal.data[index])
    getPersonal.data.splice(index)
  },
})

export const translate = createResource({
  method: "GET",
  url: "/api/method/drive.api.files.get_translate",
  cache: "translate",
  auto: true,
})
