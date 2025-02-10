import router from "@/router"
import store from "@/store"
import { formatSize, formatDate } from "@/utils/format"
import { useTimeAgo } from "@vueuse/core"

export const openEntity = (team, entity) => {
  if (entity.is_group) {
    router.push({
      name: "Folder",
      params: { team, entityName: entity.name },
    })
  } else if (entity.mime_type === "frappe_doc") {
    router.push({
      name: "Document",
      params: { entityName: entity.name },
    })
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

export const prettyData = (entities) => {
  return entities.map((entity) => {
    entity.file_size_pretty = formatSize(entity.file_size)
    entity.relativeModified = useTimeAgo(entity.modified)
    if (entity.accessed) entity.relativeAccessed = useTimeAgo(entity.accessed)
    entity.modified = formatDate(entity.modified)
    entity.creation = formatDate(entity.creation)
    entity.owner =
      entity.owner === store.state.auth.user_id ? "You" : entity.owner
    return entity
  })
}
