import { createResource } from "frappe-ui"

export const toggleFav = createResource({
  url: "drive.api.files.set_favourite",
  makeParams({ entities }) {
    return {
      entities,
    }
  },
})
