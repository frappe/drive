import { createResource, useList } from "frappe-ui"
import { toast } from "@/utils/toasts"
import { openEntity, setTitle } from "@/utils/files"
import store from "@/store"
import router from "@/router"
import { prettyData, setCache } from "@/utils/files"
import { updateURLSlug } from "@/utils/files"

// GETTERS
export const COMMON_OPTIONS = {
  method: "GET",
  debounce: 500,
  transform(data) {
    return prettyData(data)
  },
}

export const getTeam = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return {
      ...params,
      personal: 0,
    }
  },
  cache: "team-folder-contents",
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

export const getPersonal = useList({
  ...COMMON_OPTIONS,
  url: "/api/method/drive.api.list.files",
  params: {
    personal: 1,
  },
  limit: 100,
  cacheKey: "personal-folder-contents",
})

export const getFavourites = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "favourite-folder-contents",
  makeParams: (params) => {
    return { ...params, favourites_only: 1 }
  },
})

export const getDocuments = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return { ...params, file_kinds: '["Frappe Document"]' }
  },
  cache: "document-folder-contents",
})

export const getSlides = createResource({
  ...COMMON_OPTIONS,
  url: "slides.slides.doctype.presentation.presentation.get_all_presentations",
  cache: "slides-folder-contents",
  transform(data) {
    data = data.map((k) => ({
      ...k,
      mime_type: "frappe/slides",
      file_type: "Presentation",
      path: k.name,
      external: true,
      file_size: 0,
    }))
    prettyData(data)
    return data
  },
})

export const getShared = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "shared-folder-contents",
  params: { shared: "by" },
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
  getTeam,
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

export const updateMoved = (team, new_parent, special) => {
  if (!special) {
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
    }).fetch(
      store.state.sortOrder[new_parent]
        ? {
            order_by:
              store.state.sortOrder[new_parent].field +
              (store.state.sortOrder[new_parent].ascending ? " 1" : " 0"),
          }
        : {}
    )
  } else {
    ;(move.params.is_private ? getPersonal : getTeam).fetch({ team })
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
  onError: () => {
    toast({
      message: "There was an error while clearing recents.",
      type: "error",
    })
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
  onError(error) {
    toast({
      text: JSON.stringify(error),
      error: true,
    })
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
  onSuccess: () => {
    let l = store.state.breadcrumbs[store.state.breadcrumbs.length - 1]
    if (l.name === rename.params.entity_name) {
      l.label = rename.params.new_title
      store.state.activeEntity.title = rename.params.new_title
      store.state.activeEntity.modified = new Date()
      setTitle(rename.params.new_title)
      updateURLSlug(rename.params.new_title)
    }
  },
  onError(error) {
    toast({
      title: error.messages[error.messages.length - 1],
      position: "bottom-right",
      type: "error",
      timeout: 2,
    })
  },
})

export const createDocument = createResource({
  method: "POST",
  url: "drive.api.files.create_document_entity",
  makeParams: (params) => params,
})

export const createPresentation = createResource({
  method: "POST",
  url: "drive.api.files.create_presentation",
})

export const move = createResource({
  url: "drive.api.files.move",
  onSuccess(data) {
    toast({
      title: "Moved to " + data.title,
      buttons: [
        {
          label: "Go",
          onClick: () => {
            if (!data.special)
              openEntity({
                name: data.name,
                is_group: true,
              })
            else router.push({ name: data.title })
          },
        },
      ],
    })

    // Update moved-into folder
    updateMoved(data.team, data.name, data.special)
  },
  onError() {
    toast({ title: "There was an error.", type: "error" })
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
    })),
})

export const translate = createResource({
  method: "GET",
  url: "/api/method/drive.api.files.get_translate",
  cache: "translate",
})

export const storageBar = createResource({
  url: "drive.api.storage.storage_bar_data",
  method: "GET",
  cache: "total_storage",
})

setCache(getTeam, "home-folder-contents")
setCache(getShared, "shared-folder-contents")
setCache(getRecents, "recents-folder-contents")
setCache(getFavourites, "favourite-folder-contents")
setCache(getPersonal, "personal-folder-contents")
setCache(getTrash, "trash-folder-contents")
setCache(getDocuments, "document-folder-contents")
