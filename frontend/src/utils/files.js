import router from "@/router"
import store from "@/store"
import { formatSize, formatDate } from "@/utils/format"
import { useTimeAgo } from "@vueuse/core"
import { mutate, getRecents } from "@/resources/files"
import { getLink } from "./getLink"
import { getTeams } from "../resources/files"

export const openEntity = (team = null, entity, new_tab = false) => {
  if (!team) team = entity.team
  if (!entity.is_group) {
    getRecents.setData((data) => [...data, entity])
    mutate([entity], (e) => (e.accessed = true))
  }
  if (new_tab) {
    return window.open(getLink(entity, false), "_blank")
  }
  if (entity.is_group) {
    router.push({
      name: "Folder",
      params: { team, entityName: entity.name },
    })
  } else if (entity.is_link) {
    const origin = new URL(entity.path).origin
    confirm(
      `This will open an external link to ${origin} - are you sure you want to open?`
    ) && window.open(entity.path, "_blank")
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

    return entity
  })
}
export const setBreadCrumbs = (
  breadcrumbs,
  is_private,
  final_func = () => {}
) => {
  const route = router.currentRoute.value
  let res = [
    {
      label: "Shared",
      route: store.getters.isLoggedIn && "/shared",
    },
  ]
  const lastEl = breadcrumbs[breadcrumbs.length - 1]
  const partOfTeam =
    getTeams.data && Object.keys(getTeams.data).includes(lastEl.team)
  if (
    (partOfTeam && !lastEl.is_private) ||
    lastEl.owner == store.state.auth.user_id
  ) {
    res = [
      {
        label: is_private ? "Home" : getTeams.data[breadcrumbs[0].team].title,
        name: is_private ? "Home" : "Team",
        route: `/t/${route.params.team}` + (is_private ? "/" : "/team"),
      },
    ]
  }
  if (!breadcrumbs[0].parent_entity) breadcrumbs.splice(0, 1)
  breadcrumbs.forEach((item, idx) => {
    res.push({
      label: item.title,
      onClick: final_func,
      route:
        idx !== breadcrumbs.length - 1
          ? `/t/${item.team}/folder/` + item.name
          : null,
    })
  })
  store.commit("setBreadcrumbs", res)
}

export const MIME_LIST_MAP = {
  Image: [
    "image/png",
    "image/jpeg",
    "image/svg+xml",
    "image/heic",
    "image/heif",
    "image/avif",
    "image/webp",
    "image/tiff",
    "image/gif",
  ],
  PDF: ["application/pdf"],
  Text: [
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
    "application/javascript",
    "text/rich-text",
    "text/x-shellscript",
    "text/markdown",
    "application/json",
    "application/x-httpd-php",
    "text/x-python",
    "application/x-python-script",
    "application/x-sql",
    "text/x-perl",
    "text/x-csrc",
    "text/x-sh",
  ],
  "XML Data": ["application/xml"],
  Document: [
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.apple.pages",
    "application/x-abiword",
    "frappe_doc",
  ],
  Spreadsheet: [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
    "text/csv",
    "application/vnd.apple.numbers",
  ],
  Presentation: [
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.presentation",
    "application/vnd.apple.keynote",
  ],
  Audio: [
    "audio/mpeg",
    "audio/wav",
    "audio/x-midi",
    "audio/ogg",
    "audio/mp4",
    "audio/mp3",
  ],
  Video: [
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "video/x-matroska",
  ],
  Book: ["application/epub+zip", "application/x-mobipocket-ebook"],
  Application: [
    "application/octet-stream",
    "application/x-sh",
    "application/vnd.microsoft.portable-executable",
  ],
  Archive: [
    "application/zip",
    "application/x-rar-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-bzip2",
  ],
}
