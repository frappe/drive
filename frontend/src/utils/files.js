import router from "@/router"
import store from "@/store"
import { formatSize, formatDate } from "@/utils/format"
import { useTimeAgo } from "@vueuse/core"

export const openEntity = (team = null, entity) => {
  if (!team) team = "shared"
  if (entity.is_group) {
    router.push({
      name: "Folder",
      params: { team, entityName: entity.name },
    })
  } else if (entity.mime_type === "frappe_doc") {
    router.push({
      name: "Document",
      params: { team, entityName: entity.name },
    })
  } else {
    router.push({
      name: "File",
      params: { team, entityName: entity.name },
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
export const setBreadCrumbs = (breadcrumbs, is_private, file = true) => {
  const route = router.currentRoute.value
  let res = [
    {
      label: "Shared",
      route: "/shared",
    },
  ]
  if (breadcrumbs[0].parent_entity === null) {
    res = [
      {
        label: is_private ? "My Files" : "Home",
        route: `/${route.params.team}` + (is_private ? "/personal" : ""),
      },
    ]
    breadcrumbs.shift()
  }
  breadcrumbs.forEach((item, idx) => {
    res.push({
      label: item.title,
      route:
        `/${route.params?.team}/${
          idx === breadcrumbs.length - 1 ? (file ? "file" : "doc") : "folder"
        }/` + item.name,
    })
  })
  store.commit("setBreadcrumbs", res)
}
