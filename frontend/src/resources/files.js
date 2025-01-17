import { createResource } from "frappe-ui"
import { toast } from "@/utils/toasts"
import { formatSize, formatDate } from "@/utils/format"
import { useTimeAgo } from "@vueuse/core"

import store from "@/store"

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
      this.$router.replace({ name: "Error" })
    }
  },
  transform(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size
      if (entity.is_group) {
        if (entity.item_count === 0 || entity.item_count > 0) {
          entity.file_size = entity.item_count + " item"
          if (entity.item_count > 1) {
            entity.file_size = entity.item_count + " items"
          }
        } else {
          entity.file_size = ""
        }
      } else {
        entity.file_size = formatSize(entity.file_size)
      }
      entity.relativeModified = useTimeAgo(entity.modified)
      entity.modified = formatDate(entity.modified)
      entity.creation = formatDate(entity.creation)
      entity.owner = true ? "You" : entity.full_name
    })
  },
}
export const getHome = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "home-folder-contents",
})

export const getRecents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  cache: "recent-folder-contents",
  makeParams: (params) => {
    return { ...params, recents_only: true }
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
  url: "drive.api.list.shared_with_user",
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
  makeParams({ entities }) {
    return {
      entities,
    }
  },
  onSuccess() {
    if (toggleFav.params.entities[0].is_favourite === false) {
      toast(
        `${
          toggleFav.params.entities.length > 1
            ? toggleFav.params.entities.length + " items removed"
            : "Removed"
        } from Favourites`
      )
    } else {
      toast(
        `${
          toggleFav.params.entities.length > 1
            ? toggleFav.params.entities.length + " items added"
            : "Added"
        } to Favourites`
      )
    }
  },
})

export const clearRecent = createResource({
  url: "drive.api.files.remove_recents",
  makeParams: ({ entities }) => ({
    entity_names: entities.map((e) => e.name),
  }),
  onSuccess: () =>
    clearRecent.params.entities.length > 1
      ? toast(`Cleared  ${entities.length} files from Recents`)
      : null,
})
