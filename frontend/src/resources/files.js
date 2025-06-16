import { createResource } from "frappe-ui"
import { toast } from "@/utils/toasts"
import { openEntity } from "@/utils/files"

import store from "@/store"
import router from "@/router"
import { prettyData, setCache } from "@/utils/files"

// GETTERS
export const COMMON_OPTIONS = {
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
    return prettyData(data)
  },
}

export const getHome = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return {
      ...params,
      personal: 0,
    }
  },
  cache: "home-folder-contents",
})

export const getTeams = createResource({
  url: "/api/method/drive.api.permissions.get_teams",
  params: {
    details: 1,
  },
  method: "GET",
  cache: "teams",
})

export const getRecents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "recents-folder-contents",
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
    return { ...params, is_active: 0, only_parent: 0 }
  },
})

// SETTERS
export const LISTS = [
  getPersonal,
  getHome,
  getRecents,
  getShared,
  getFavourites,
]
export const mutate = (entities, func) => {
  LISTS.forEach((l) =>
    l.setData((d) => {
      if (!d) return
      entities.forEach(({ name, ...params }) => {
        let el = d.find((k) => k.name === name)
        if (el) {
          func(el, params)
        }
      })
      return d
    })
  )
}

export const updateMoved = (new_parent, team) => {
  if (new_parent && team) {
    // All details are repetetively provided (check Folder.vue) because if this is run first
    // No further mutation of the resource object can take place
    createResource({
      ...COMMON_OPTIONS,
      url: "drive.api.list.files",
      makeParams: (params) => ({
        ...params,
        entity_name: new_parent,
        personal: -2,
        team,
      }),
      cache: ["folder", new_parent],
    }).fetch({
      order_by:
        store.state.sortOrder.field +
        (store.state.sortOrder.ascending ? " 1" : " 0"),
    })
  } else {
    ;(move.params.is_private ? getPersonal : getHome).fetch({ team })
  }
}

export const toggleFav = createResource({
  url: "drive.api.files.set_favourite",
  makeParams(data) {
    if (!data) {
      getFavourites.setData([])
      mutate(getFavourites.data, (el) => (el.is_favourite = false))
      return { clear_all: true }
    }
    const entity_names = data.entities.map(({ name }) => name)
    getFavourites.setData((d) => {
      return data.entities[0].is_favourite
        ? [...d, ...data.entities]
        : d.filter(({ name }) => !entity_names.includes(name))
    })
    mutate(
      data.entities,
      (el, { is_favourite }) => (el.is_favourite = is_favourite)
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
  makeParams: (data) => {
    if (!data) {
      getRecents.setData([])
      return { clear_all: true }
    }
    const entity_names = data.entities.map(({ name }) => name)
    getRecents.setData((d) =>
      d.filter(({ name }) => !entity_names.includes(name))
    )
    return {
      entity_names,
    }
  },
  onSuccess: () => {
    const files = clearRecent.params.entity_names?.length
    toast(
      `Removed  ${files || "all"} file${files === 1 ? "" : "s"} from Recents.`
    )
  },
})

export const clearTrash = createResource({
  url: "drive.api.files.delete_entities",
  makeParams: (data) => {
    if (!data) {
      getTrash.setData([])
      return { clear_all: true }
    }
    return { entity_names: data.entities.map((e) => e.name) }
  },
  onSuccess: () => {
    // Buggy for some reason
    const files = clearTrash.params.entity_names?.length
    toast(
      `Permanently deleted ${files || "all"} file${files === 1 ? "" : "s"}.`
    )
  },
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
  onError(error) {
    toast({
      title: JSON.stringify(error).includes("FileExistsError")
        ? "There is already a file with this name!"
        : "There was an error",
      position: "bottom-right",
      timeout: 2,
    })
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
    getHome.setData((data) => {
      data.push(getPersonal.data[index])
      return data
    })

    getPersonal.setData((data) => {
      data.splice(index, 1)
      return data
    })
  },
})

export const move = createResource({
  url: "drive.api.files.move",
  onSuccess(data) {
    toast({
      title: "Moved to " + data.title,
      buttons: [
        {
          label: "Go",
          action: () => {
            openEntity(null, {
              name: data.name,
              team: data.team,
              is_group: true,
              is_private: data.is_private,
            })
          },
        },
      ],
    })

    // Update moved-into folder
    updateMoved(data.name, data.team, data.is_private)
  },
  onError() {
    toast("There was an error.")
  },
})

export const allFolders = createResource({
  method: "GET",
  url: "drive.api.list.files",
  cache: "all-folders",
  makeParams: (params) => ({
    ...params,
    is_active: 1,
    folders: 1,
    personal: -1,
    only_parent: 0,
  }),
  transform: (d) =>
    d.map((k) => ({
      value: k.name,
      label: k.title,
      parent: k.parent_entity,
      is_private: k.is_private,
    })),
})

export const translate = createResource({
  method: "GET",
  url: "/api/method/drive.api.files.get_translate",
  cache: "translate",
})

setCache(getHome, "home-folder-contents")
setCache(getShared, "shared-folder-contents")
setCache(getRecents, "recents-folder-contents")
setCache(getFavourites, "favourite-folder-contents")
setCache(getPersonal, "personal-folder-contents")
setCache(getTrash, "trash-folder-contents")
