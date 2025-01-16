import { createResource } from "frappe-ui"

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

export const getFiles = createResource({
  url: "drive.api.files.get",
  makeParams({ folder }) {
    return {
      folder,
    }
  },
})
