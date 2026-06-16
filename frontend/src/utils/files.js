import router from '@/router'
import store from '@/store'
import { formatSize } from '@/utils/format'
import { nextTick } from 'vue'
import { useTimeAgo } from '@vueuse/core'
import { getFileLink } from '@/ui/drive/js/utils'
import {
  getRecents,
  mutate,
  createDocument,
  getDocuments,
} from '@/resources/files'
import { getTeams, getPublicTeams } from '@/resources/files'
import { set } from 'idb-keyval'
import { toast } from '@/utils/toasts.js'
import { useFileUpload, toast as nToast } from 'frappe-ui'
import emitter from '@/emitter'

import folderIcon from '@icons/folder.svg'
import imageIcon from '@icons/image.svg'
import pdfIcon from '@icons/pdf.svg'
import photoshopIcon from '@icons/photoshop.svg'
import codeIcon from '@icons/code.svg'
import sketchIcon from '@icons/sketch.svg'
import markdownIcon from '@icons/markdown.svg'
import textIcon from '@icons/text.svg'
import documentIcon from '@icons/document.svg'
import spreadsheetIcon from '@icons/spreadsheet.svg'
import presentationIcon from '@icons/presentation.svg'
import audioIcon from '@icons/audio.svg'
import videoIcon from '@icons/video.svg'
import applicationIcon from '@icons/application.svg'
import archiveIcon from '@icons/archive.svg'
import unknownIcon from '@icons/unknown.svg'

const FILE_ICONS = {
  Folder: folderIcon,
  Image: imageIcon,
  PDF: pdfIcon,
  Photoshop: photoshopIcon,
  Code: codeIcon,
  Sketch: sketchIcon,
  Markdown: markdownIcon,
  Text: textIcon,
  Document: documentIcon,
  Spreadsheet: spreadsheetIcon,
  Presentation: presentationIcon,
  Audio: audioIcon,
  Video: videoIcon,
  Application: applicationIcon,
  Archive: archiveIcon,
}

export const WRITER_CONTENT_DOCTYPE = 'Writer Document'
export const PRESENTATION_CONTENT_DOCTYPE = 'Presentation'
export const ATTACHMENT_CONTENT_DOCTYPE = 'File'

export function isWriterDocument(entity) {
  return entity?.content_doctype === WRITER_CONTENT_DOCTYPE
}

export function isPresentation(entity) {
  return entity?.content_doctype === PRESENTATION_CONTENT_DOCTYPE
}

export function hasHostedContent(entity) {
  return isWriterDocument(entity) || isPresentation(entity)
}

export function isManaged(entity) {
  return entity?.kind === 'native'
}

export function isReadonly(entity) {
  return entity?.kind === 'readonly'
}

export function isSiteFile(entity) {
  return !entity?.team
}

export function isAttachmentRef(entity) {
  return entity?.content_doctype === ATTACHMENT_CONTENT_DOCTYPE
}

export function isVirtual(entity) {
  return entity?.kind === 'virtual'
}

export const openEntity = (entity, new_tab = false) => {
  // Virtual grouping node: navigate into its attachments bucket. A node with an
  // attached_to_name drills into a single document; otherwise into a doctype.
  if (isVirtual(entity)) {
    return router.push({
      name: 'Attachments',
      params: entity.attached_to_name
        ? {
            doctype: entity.attached_to_doctype,
            docname: entity.attached_to_name,
          }
        : { doctype: entity.attached_to_doctype },
    })
  }

  if (!entity.is_folder) {
    if (!getRecents.data?.some?.((k) => k.name === entity.name))
      getRecents.setData((data) => [...(data || []), entity])

    mutate([entity], (e) => {
      e.accessed = Date()
      entity.relativeAccessed = useTimeAgo(entity.accessed)
    })
  }

  if (new_tab) {
    return window.open(getFileLink(entity, false), '_blank')
  }
  if (!['Link', 'Presentation'].includes(entity.file_type)) {
    if (!entity.breadcrumbs?.length)
      store.state.breadcrumbs.push({
        label: entity.file_name,
        name: entity.name,
        route: null,
      })
    else setBreadCrumbs(entity)
  }

  // hm?
  if (entity.name === '') {
    router.push({
      name: entity.is_private ? 'Home' : 'Team',
      params: { team },
    })
  } else if (entity.is_folder) {
    router.push({
      name: 'Folder',
      params: { entityName: entity.name },
    })
  } else if (entity.file_type === 'Link') {
    const origin = new URL(entity.file_url).origin
    if (
      confirm(
        `This will open an external link to ${origin} - are you sure you want to open?`
      )
    )
      window.open(entity.file_url, '_blank')
  } else if (entity.file_type === 'Presentation') {
    window.location.href = '/slides/presentation/' + entity.file_url
  } else if (
    entity.file_type === 'Document' ||
    entity.file_type === 'Markdown'
  ) {
    window.location.href = '/writer/w/' + entity.name
  } else {
    router.push({
      name: 'File',
      params: { entityName: entity.name },
    })
  }
}

function trimCommonPrefix(a, b) {
  let i = 0
  while (i < a.length && i < b.length && !/^\d+$/.test(a[i]) && a[i] === b[i])
    i++
  return [
    a.slice(i).split(/[\W]/)[0].toLowerCase(),
    b.slice(i).split(/[\W]/)[0].toLowerCase(),
  ]
}

function extractNum(name) {
  const match = name.match(/^(.*?)(\d+)(\D*)$/)
  if (!match) return 0
  return parseInt(match[2], 10)
}
const months = {
  january: 1,
  jan: 1,
  february: 2,
  feb: 2,
  march: 3,
  mar: 3,
  april: 4,
  apr: 4,
  may: 5,
  june: 6,
  jun: 6,
  july: 7,
  jul: 7,
  august: 8,
  aug: 8,
  september: 9,
  sep: 9,
  sept: 9,
  october: 10,
  oct: 10,
  november: 11,
  nov: 11,
  december: 12,
  dec: 12,
}

const days = {
  sunday: 7,
  sun: 7,
  monday: 1,
  mon: 1,
  tuesday: 2,
  tue: 2,
  tues: 2,
  wednesday: 3,
  wed: 3,
  thursday: 4,
  thu: 4,
  thurs: 4,
  friday: 5,
  fri: 5,
  saturday: 6,
  sat: 6,
}

function extractTime(n) {
  if (months[n]) return months[n]
  if (days[n]) return days[n]

  return 0
}

export const sortEntities = (rows, order) => {
  if (!order) order = store.state.sortOrder
  // Mutates directly
  const field = order.field
  const asc = order.ascending ? 1 : -1
  rows.sort((a, b) => {
    return a[field] == b[field] ? 0 : a[field] > b[field] ? asc : -asc
  })
  if (order.smart) {
    rows.sort((a, b) => {
      const [endA, endB] = trimCommonPrefix(a.file_name, b.file_name)
      if (!endA) return 0
      const numA = extractNum(endA)
      const numB = extractNum(endB)
      if (numA && numB) return (numA - numB) * asc

      const timeA = extractTime(endA)
      const timeB = extractTime(endB)
      if (timeA && timeB) return (timeA - timeB) * asc

      return 0
    })
  }
  return rows
}

export const groupByFolder = (entities) => {
  return {
    Folders: entities.filter((x) => x.is_folder === 1),
    Files: entities.filter((x) => x.is_folder === 0),
  }
}

export const prettyData = (entities) => {
  return entities.map((entity) => {
    entity.file_size_pretty = formatSize(entity.file_size)
    entity.relativeModified = useTimeAgo(entity.modified)
    if (entity.accessed) entity.relativeAccessed = useTimeAgo(entity.accessed)
    return entity
  })
}
export const setBreadCrumbs = (entity) => {
  let breadcrumbs = entity.breadcrumbs
  const in_home = entity.in_home
  const team =
    getTeams.data?.[breadcrumbs[0].team] ||
    getPublicTeams.data?.[breadcrumbs[0].team]

  let res = []
  if (entity.attached_to_doctype) {
    // Framework attachments live under Home/Attachments; surface their real
    // location (Attachments > Doctype > Document) instead of "Shared".
    res = [
      {
        label: __('Attachments'),
        name: 'Attachments',
        route: { name: 'Attachments' },
      },
      {
        label: entity.attached_to_doctype,
        name: entity.attached_to_doctype,
        route: {
          name: 'Attachments',
          params: { doctype: entity.attached_to_doctype },
        },
      },
    ]
    if (entity.attached_to_name) {
      res.push({
        label: entity.attached_to_name,
        name: entity.attached_to_name,
        route: {
          name: 'Attachments',
          params: {
            doctype: entity.attached_to_doctype,
            docname: entity.attached_to_name,
          },
        },
      })
    }
    // Drop the folder-based upward path; only the file itself follows above.
    breadcrumbs = breadcrumbs.slice(-1)
  } else if (team || in_home) {
    res = [
      {
        label: in_home ? __('Home') : team.title,
        name: in_home ? 'Home' : team.name,
        route: in_home
          ? { name: 'Home' }
          : { name: 'Team', params: { team: team.name } },
      },
    ]
  } else if (entity.folder === 'Home/Attachments' || entity.folder === 'Home') {
    res = [
      {
        label: __('Shared'),
        name: 'Shared',
        route: '/shared',
      },
    ]
  } else if (store.getters.isLoggedIn) {
    res = [
      {
        label: __('Shared'),
        name: 'Shared',
        route: '/?shared=1',
      },
    ]
  }

  if (!breadcrumbs[0].folder) breadcrumbs.splice(0, 1)
  const popBreadcrumbs = (item) => () =>
    res.splice(res.findIndex((k) => k.name === item.name) + 1)

  breadcrumbs.forEach((folder, idx) => {
    const final = idx === breadcrumbs.length - 1
    res.push({
      label: folder.file_name,
      name: folder.name,
      onClick: final
        ? () => entity.write && emitter.emit('rename')
        : popBreadcrumbs(folder),
      route: final
        ? null
        : { name: 'Folder', params: { entityName: folder.name } },
    })
  })
  store.commit('setBreadcrumbs', res)
}

export function getIconUrl(file_type) {
  return FILE_ICONS[file_type] ?? unknownIcon
}

// `src` is the thumbnail (images/videos/PDFs) or the icon; `fallback` is the icon.
export function getThumbnailUrl({ name, file_type, thumbnail, external }, view = 'list') {
  const fallback = getIconUrl(file_type ?? 'Presentation')
  let src = ''
  if (external) src = view !== 'list' ? thumbnail : ''
  else if (['Image', 'Video', 'PDF'].includes(file_type))
    src = `/api/method/drive.api.files.get_thumbnail?entity_name=${name}`
  return { src: src || fallback, fallback }
}

export const MIME_LIST_MAP = {
  Folder: [],
  Image: [
    'image/png',
    'image/jpeg',
    'image/svg+xml',
    'image/heic',
    'image/heif',
    'image/avif',
    'image/webp',
    'image/tiff',
    'image/gif',
  ],
  PDF: ['application/pdf'],
  'After Effects': ['application/vnd.adobe.aftereffects.project'],
  Photoshop: ['application/photoshop'],
  Code: [
    'text/x-python',
    'text/x-shellscript',
    'application/x-httpd-php',
    'application/x-python-script',
    'application/x-sql',
    'text/html',
    'text/css',
    'text/javascript',
    'application/javascript',
  ],
  Sketch: ['application/sketch'],
  Markdown: ['text/markdown'],
  Text: [
    'text/plain',

    'text/rich-text',
    'application/json',

    'text/x-perl',
    'text/x-csrc',
    'text/x-sh',
  ],
  'XML Data': ['application/xml'],
  Document: [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.apple.pages',
    'application/x-abiword',
    'frappe_doc',
  ],
  Spreadsheet: [
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.oasis.opendocument.spreadsheet',
    'text/csv',
    'application/vnd.apple.numbers',
  ],
  Presentation: [
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.apple.keynote',
  ],
  Audio: [
    'audio/mpeg',
    'audio/wav',
    'audio/x-midi',
    'audio/ogg',
    'audio/mp4',
    'audio/mp3',
  ],
  Video: [
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
    'video/x-matroska',
  ],
  Book: ['application/epub+zip', 'application/x-mobipocket-ebook'],
  Application: [
    'application/octet-stream',
    'application/x-sh',
    'application/vnd.microsoft.portable-executable',
  ],
  Archive: [
    'application/zip',
    'application/x-rar-compressed',
    'application/x-tar',
    'application/gzip',
    'application/x-bzip2',
  ],
}

// Synced cache - ensure all setters are reflected in the app
function getCacheKey(cacheKey) {
  if (!cacheKey) {
    return null
  }
  if (typeof cacheKey === 'string') {
    cacheKey = [cacheKey]
  }
  return JSON.stringify(cacheKey)
}
export function setCache(t, cache) {
  t.setData = async (data) => {
    if (typeof data === 'function') {
      t.data = data(t.data)
    } else {
      t.data = data
    }
    await set(getCacheKey(cache), JSON.stringify(t.data))
  }
}

export function enterFullScreen() {
  let elem = document.getElementById('renderContainer')
  if (elem.requestFullscreen) {
    elem.requestFullscreen()
  } else if (elem.mozRequestFullScreen) {
    /* Firefox */
    elem.mozRequestFullScreen()
  } else if (elem.webkitRequestFullscreen) {
    /* Chrome, Safari & Opera */
    elem.webkitRequestFullscreen()
  } else if (elem.msRequestFullscreen) {
    /* IE/Edge */
    elem.msRequestFullscreen()
  }
}

function slugger(file_name) {
  return file_name
    .split('.')
    .join(' ')
    .toLowerCase()
    .trim()
    .replace(/[^\w\s']|_/g, '')
    .replace(/\s+/g, '-')
}

function getLinkStem(entity) {
  return `${
    {
      true: 'f',
      [new Boolean(entity.is_folder)]: 'd',
      [new Boolean(isWriterDocument(entity) || entity.mime_type === 'text/markdown')]: 'w',
    }[true]
  }/${entity.name}/${slugger(entity.file_name)}`
}

const copyToClipboard = (str) => {
  if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(str)
  } else {
    // Fallback to the legacy clipboard API
    const textArea = document.createElement('textarea')
    textArea.value = str
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    return Promise.resolve()
  }
}

export async function updateURLSlug(file_name) {
  const route = router.currentRoute.value
  await nextTick()
  const slug = slugger(file_name)
  if (route.params.slug !== slug) {
    // Hacky, but we only want to update the URL - triggering a reload breaks a lot
    const base = window.location.pathname.split('/').slice(0, 4).join('/')
    const new_path = base + (base.endsWith('/') ? '' : '/') + slug
    history.replaceState({}, null, new_path)
  }
}

export function getLink(entity, copy = true, withDomain = true) {
  let link
  if (entity.file_type === 'Link') link = entity.file_url
  else if (entity.mime_type === 'frappe/slides') {
    link = window.location.origin + '/slides/presentation/' + entity.name
  } else if (
    entity.file_type === 'Document' ||
    entity.file_type === 'Markdown'
  ) {
    link = window.location.origin + '/writer/w/' + entity.name
  } else {
    link = `${
      withDomain ? window.location.origin + '/drive' : ''
    }/${getLinkStem(entity)}`
  }
  if (!copy) return link
  try {
    copyToClipboard(link).then(() => toast('Copied to your clipboard.'))
  } catch (err) {
    if (err.name === 'NotAllowedError') {
      toast({
        icon: 'alert-triangle',
        iconClasses: 'text-ink-red-3',
        title: 'Clipboard permission denied',
        position: 'bottom-right',
      })
    } else {
      console.error('Failed to copy link:', err)
    }
  }
}

export function dynamicList(k) {
  return k.filter((a) => typeof a !== 'object' || !('cond' in a) || a.cond)
}

export const setTitle = (file_name) =>
  (document.title =
    (router.currentRoute.value.name === 'Folder' ? 'Folder - ' : '') +
    file_name)

async function uploadImage(file, params) {
  const uploader = useFileUpload()
  const upload = uploader.upload(file, {
    params,
    upload_endpoint: '/api/method/drive.api.files.upload_file',
  })
  let entity = await new Promise((resolve) => {
    upload.then((data) => {
      resolve(data)
    })
  })

  return entity
}

export const pasteObj = (e) => {
  const clipboardItems = Array.from(e.clipboardData?.items || [])
  if (clipboardItems.some((item) => item.type.includes('image'))) {
    e.preventDefault()
    const file = clipboardItems
      .find((item) => item.type.includes('image'))
      ?.getAsFile()
    const route = router.currentRoute.value
    if (file && ['Home', 'Folder', 'Team'].includes(route.name)) {
      const entity = uploadImage(file, {
        team: route.params.team,
        parent: route.params.entityName || '',
        personal: store.state.breadcrumbs[0].name === 'Home' ? 1 : 0,
        total_file_size: file.size,
        file_modified: file.lastModified,
      })
      nToast.promise(entity, {
        loading: 'Uploading...',
        success: () => {
          emitter.emit('refresh')
          return 'Uploaded'
        },
        error: () => 'Failed to upload',
        duration: 500,
      })
    }
  }
}

export const FONT_FAMILIES = [
  {
    label: 'Caveat',
    value: 'caveat',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-caveat)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-caveat)',
      }),
  },
  {
    label: 'Comic Sans',
    value: 'comic-sans',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-comic-sans)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-comic-sans)',
      }),
  },
  {
    label: 'Comfortaa',
    value: 'comfortaa',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-comfortaa)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-comfortaa)',
      }),
  },
  {
    label: 'EB Garamond',
    value: 'eb-garamond',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-eb-garamond)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-eb-garamond)',
      }),
  },
  {
    label: 'Fantasy',
    value: 'fantasy',
    action: (editor) => editor.chain().focus().setFontFamily('fantasy').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'fantasy',
      }),
  },
  {
    label: 'Geist',
    value: 'geist',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-geist)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-geist)',
      }),
  },
  {
    label: 'IBM Plex Sans',
    value: 'ibm-plex',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-ibm-plex)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-ibm-plex)',
      }),
  },
  {
    label: 'Inter',
    value: 'inter',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-inter)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-inter)',
      }),
  },
  {
    label: 'JetBrains Mono',
    value: 'jetbrains',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-jetbrains)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-jetbrains)',
      }),
  },
  {
    label: 'Lora',
    value: 'lora',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-lora)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-lora)',
      }),
  },
  {
    label: 'Merriweather',
    value: 'merriweather',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-merriweather)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-merriweather)',
      }),
  },
  {
    label: 'Nunito',
    value: 'nunito',
    action: (editor) =>
      editor.chain().focus().setFontFamily('var(--font-nunito)').run(),
    isActive: (editor) =>
      editor.isActive('textStyle', {
        fontFamily: 'var(--font-nunito)',
      }),
  },
]

export function getRandomColor() {
  const letters = '0123456789ABCDEF'
  let color = '#'
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 10)]
  }
  return color
}
export const newExternal = async (type) => {
  const route = router.currentRoute.value
  if (type === 'Presentation') {
    window.location.href = `/slides/presentation/new?parent=${
      store.state.currentFolder.name
    }&team=${route.params.team || ''}`
    return
  }
  const data = await createDocument.submit({
    team: route.params.team,
    parent: store.state.currentFolder.name,
  })
  prettyData([data])
  data.file_type = type
  store.state.listResource.data?.push?.(data)
  getDocuments.data?.push?.(data)
  window.location.href = '/writer/w/' + data.name
}

function isApple() {
  // Pattern borrowed from TinyKeys library.
  // --
  // https://github.com/jamiebuilds/tinykeys/blob/e0d23b4f248af59ffbbe52411505c3d681c73045/src/tinykeys.ts#L50-L54
  var macOsPattern = /Mac|iPod|iPhone|iPad/

  return macOsPattern.test(window.navigator.platform)
}

export function isModKey(e) {
  return isApple() ? e.metaKey : e.ctrlKey
}
