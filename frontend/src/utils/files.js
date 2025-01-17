import router from "@/router"

export const openEntity = (entity) => {
  if (entity.is_group) {
    router.push({
      name: "Folder",
      params: { entityName: entity.name },
    })
  } else if (entity.mime_type === "frappe_doc") {
    if (this.$store.state.editorNewTab) {
      window.open(
        router.resolve({
          name: "Document",
          params: { entityName: entity.name },
        }).href,
        "_blank"
      )
    } else {
      router.push({
        name: "Document",
        params: { entityName: entity.name },
      })
    }
  } else if (entity.mime_type === "frappe_whiteboard") {
    router.push({
      name: "Whiteboard",
      params: { entityName: entity.name },
    })
  } else {
    router.push({
      name: "File",
      params: { entityName: entity.name },
    })
  }
}

export const groupByFolder = (entities) => {
  return {
    Folders: entities.filter((x) => x.is_group === 1),
    Files: entities.filter((x) => x.is_group === 0),
  }
}
