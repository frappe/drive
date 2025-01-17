import { createResource, createListResource } from "frappe-ui"
import { formatSize, formatDate } from "@/utils/format"
import { useTimeAgo } from "@vueuse/core"

// GETTERS
const COMMON_OPTIONS = {
  method: "GET",
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      this.$store.commit("setError", {
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
})

export const clearRecent = createResource({
  url: "drive.api.files.remove_recents",
  makeParams({ entities }) {
    console.log(entities.map((e) => e.name))
    return {
      entity_names: entities.map((e) => e.name),
    }
  },
})
