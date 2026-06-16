<template>
  <Navbar v-if="!verify?.error && !getEntities.error" :root-resource="verify"
    :entities="activeEntity ? [activeEntity] : selectedEntitities" />

  <ErrorPage v-if="verify?.error || getEntities.error" :error="verify?.error || getEntities.error" />

  <div v-else id="drop-area" ref="container" class="flex flex-col overflow-auto min-h-full bg-surface-white">
    <DriveToolBar v-model:sort-order="sortOrder" v-model:search="search" v-model:filters="filters" v-model:team="team"
      :action-items="actionItems" :selections="selectedEntitities" :get-entities="getEntities || { data: [] }" />

    <div v-if="!props.getEntities.data" class="m-auto" style="transform: translate(0, -88.5px)">
      <LoadingIndicator class="size-5 text-ink-gray-9" />
    </div>
    <NoFilesSection v-else-if="!props.getEntities.data?.length" :icon="icon" v-bind="empty" />
    <ListView v-else-if="$store.state.view === 'list'" v-model="selections" :folder-contents="rows && grouper(rows)"
      :action-items="actionItems" :root-entity="verify?.data" @dropped="onDrop" />
    <GridView v-else v-model="selections" :folder-contents="rows" :action-items="actionItems" @dropped="onDrop" />
  </div>
  <p class="hidden absolute text-center top-1/2 left-[calc(50%-4rem)] w-32 z-10 font-bold">
    Drop to upload
  </p>
  <Transition v-if="store.state.uploads.length > 0"
    enter-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    enter-from-class="translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-1 opacity-0">
    <UploadTracker />
  </Transition>
</template>
<script setup>
import ListView from '@/components/ListView.vue'
import GridView from '@/components/GridView.vue'
import DriveToolBar from '@/components/DriveToolBar.vue'
import Navbar from '@/components/Navbar.vue'
import NoFilesSection from '@/components/NoFilesSection.vue'
import UploadTracker from '@/components/UploadTracker.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import {
  pasteObj,
  openEntity,
  prettyData,
  sortEntities,
  isVirtual,
  isManaged,
  isAttachmentRef,
  isSiteFile,
} from '@/utils/files'
import { toggleFav, clearRecent } from '@/resources/files'
import { entitiesDownload } from '@/utils/download'
import { ref, computed, watch, watchEffect, provide, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useEventListener } from '@vueuse/core'
import { useStore } from 'vuex'
import { toast } from '@/utils/toasts'
import { move } from '@/resources/files'
import { LoadingIndicator } from 'frappe-ui'
import { settings } from '@/resources/permissions'
import emitter from '@/emitter'
import { getFileLink } from '@/ui/drive/js/utils'

import LucideClock from '~icons/lucide/clock'
import LucideDownload from '~icons/lucide/download'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideEye from '~icons/lucide/eye'
import LucideInfo from '~icons/lucide/info'
import LucideLink2 from '~icons/lucide/link-2'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideRotateCcw from '~icons/lucide/rotate-ccw'
import LucideShare2 from '~icons/lucide/share-2'
import LucideSquarePen from '~icons/lucide/square-pen'
import LucideCornerLeftUp from '~icons/lucide/corner-left-up'
import LucideMonitorCog from '~icons/lucide/monitor-cog'
import LucideStar from '~icons/lucide/star'
import LucideTrash from '~icons/lucide/trash'

const props = defineProps({
  grouper: { type: Function, default: (d) => d },
  showSort: { type: Boolean, default: true },
  verify: { type: Object, default: null },
  icon: [Function, Object],
  empty: Object,
  getEntities: Object,
})
const route = useRoute()
const store = useStore()

const dialog = ref('')
provide('dialog', dialog)

const team = ref(
  ['Recents', 'Favourites', 'Trash'].includes(route.name)
    ? 'all'
    : route.params.team
)
watch(
  () => route.params.team,
  (v) => {
    team.value = v || ''
  },
  { immediate: true }
)
const activeEntity = computed(() => store.state.activeEntity)

const sortId = computed(
  () => route.params.entityName || route.params.team || route.name
)
const inIframe = inject('inIframe')
const DEFAULT_SORT = inIframe.value
  ? {
    label: 'Name',
    field: 'name',
    ascending: true,
  }
  : {
    label: 'Modified',
    field: 'modified',
    ascending: false,
  }
const sortOrder = ref(store.state.sortOrder[sortId.value] || DEFAULT_SORT)
const search = ref('')
const filters = ref([])

const rows = ref(props.getEntities.data)
watch(sortId, (id) => {
  if (store.state.sortOrder[id]) sortOrder.value = store.state.sortOrder[id]
})

watch(
  sortOrder,
  (order) => {
    rows.value = sortEntities([...rows.value], order)
    props.getEntities.setData(rows.value)
    if (sortId.value) {
      store.commit('setSortOrder', [sortId.value, order])
    }
  },
  { deep: true }
)

watch(search, (val) => {
  const search = new RegExp(val, 'i')
  rows.value = props.getEntities.data.filter((k) => search.test(k.file_name))
})

watch(
  () => filters.value,
  (val) => {
    if (!val.length) {
      rows.value = props.getEntities.data
      return
    }
    const file_types = val.map((k) => k.name)
    const isFolder = file_types.find((k) => k === 'Folder')
    rows.value = props.getEntities.data.filter(
      ({ file_type, is_folder }) =>
        file_types.includes(file_type) || (isFolder && is_folder)
    )
  },
  { deep: true }
)

watch(
  () => props.getEntities.data,
  (val) => {
    if (!val) return
    rows.value = sortEntities([...val], sortOrder.value)
    store.commit('setCurrentFolder', {
      entities: rows.value.filter?.((k) => k.file_name?.[0] !== '.'),
    })
  },
  { immediate: true, deep: true }
)

store.commit('setListResource', props.getEntities)
store.commit('setCurrentResource', null)

const selections = ref(new Set())
const selectedEntitities = computed(
  () =>
    props.getEntities.data?.filter?.(({ name }) =>
      selections.value.has(name)
    ) || []
)

const verifyAccess = computed(() => props.verify?.data || !props.verify)
watchEffect(() => {
  if (verifyAccess.value?.write) useEventListener('paste', pasteObj)
})

const refreshData = () => {
  const params = { team: team.value === 'home' ? '' : team.value || '' }
  if (sortOrder.value) {
    params.order_by = sortOrder.value.field
    params.ascending = sortOrder.value.ascending
  }
  props.getEntities.fetch({ ...props.getEntities.params, ...params })
}

watch(
  [verifyAccess, team],
  ([data]) => {
    if (!data) return
    refreshData()
  },
  { immediate: true, deep: false }
)
emitter.on('refresh', refreshData)
emitter.on('remove-file', (item) => {
  selections.value.clear()
  selections.value.add(item)
  dialog.value = 'remove'
})

if (!settings.fetched && store.getters.isLoggedIn) settings.fetch()

// Drag and drop
const removeFile = (file, target) => {
  const removedIndex = props.getEntities.data.findIndex((k) => k.name === file)
  props.getEntities.data.splice(removedIndex, 1)
  const targetRow = props.getEntities.data.find((k) => k.name === target)
  if (targetRow) targetRow.children += 1
  props.getEntities.setData(props.getEntities.data)
}
const onDrop = (targetFile, draggedItem) => {
  if (!targetFile.is_folder || draggedItem === targetFile.name || !draggedItem)
    return
  move.submit({
    entity_names: [draggedItem],
    new_parent: targetFile.name,
  })
  removeFile(draggedItem, targetFile.name)
}
emitter.on('remove-file-ui', removeFile)

// Action Items
const actionItems = computed(() => {
  if (route.name === 'Trash') {
    return [
      {
        label: 'Restore',
        icon: LucideRotateCcw,
        action: () => (dialog.value = 'restore'),
        multi: true,
        important: true,
      },
      {
        label: 'Delete forever',
        icon: LucideTrash,
        action: () => (dialog.value = 'd'),
        isEnabled: () => route.name === 'Trash',
        multi: true,
        danger: true,
      },
    ].filter((a) => !a.isEnabled || a.isEnabled())
  } else {
    return [
      {
        label: __('Preview'),
        icon: LucideEye,
        action: ([entity]) => openEntity(entity),
        isEnabled: (e) => e.file_type !== 'Link' && !isVirtual(e),
      },
      {
        label: __('Open'),
        icon: LucideExternalLink,
        action: ([entity]) => openEntity(entity),
        isEnabled: (e) => e.file_type === 'Link',
      },
      {
        label: __('Show Info'),
        icon: LucideInfo,
        action: () => (dialog.value = 'i'),
        isEnabled: (e) => !isVirtual(e),
      },
      {
        label: __('Copy Link'),
        icon: LucideLink2,
        action: ([entity]) => getFileLink(entity),
        important: true,
      },
      {
        label: __('Download'),
        icon: LucideDownload,
        // Downloading is read-only, so it is safe for every real file regardless
        // of kind (parity with the file-preview navbar). Only virtual grouping
        // nodes and non-downloadable types are excluded.
        isEnabled: (e) =>
          !isVirtual(e) &&
          !['Link', 'Presentation', 'Document'].includes(e.file_type),
        action: (entities) => entitiesDownload(entities),
        multi: true,
        important: true,
      },
      {
        divider: true,
        isEnabled: (e) =>
          isAttachmentRef(e) || (isSiteFile(e) && store.state.user.systemUser),
      },
      {
        label: __('Go to original'),
        icon: LucideCornerLeftUp,
        action: ([entity]) => {
          window.open(
            '/api/method/drive.api.files.redirect_to_original?file_id=' +
            entity.name,
            '_blank'
          )
        },
        isEnabled: (e) => isAttachmentRef(e),
      },
      {
        label: __('Open in Desk'),
        icon: LucideMonitorCog,
        action: ([entity]) =>
          window.open('/desk/file/' + entity.name, '_blank'),
        isEnabled: (e) => isSiteFile(e) && store.state.user.systemUser,
      },
      { divider: true, isEnabled: (e) => !e.external && !isVirtual(e) },
      {
        label: __('Share'),
        icon: LucideShare2,
        action: () => (dialog.value = 's'),
        isEnabled: (e) => e.share && isManaged(e),
        important: true,
      },
      {
        label: __('Rename'),
        icon: LucideSquarePen,
        action: () => (dialog.value = 'rn'),
        isEnabled: (e) => isManaged(e) && e.write,
      },
      {
        label: __('Move'),
        icon: LucideArrowLeftRight,
        action: () => (dialog.value = 'm'),
        isEnabled: (e) => isManaged(e) && e.write,
        multi: true,
        important: true,
      },
      {
        label: __('Favourite'),
        icon: LucideStar,
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = true))
          // Hack to cache
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => !e.is_favourite && !e.external && !isVirtual(e),
        important: true,
        multi: true,
      },
      {
        label: __('Unfavourite'),
        icon: LucideStar,
        class: 'text-ink-amber-3 stroke-current fill-current',
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = false))
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => e.is_favourite && !e.external && !isVirtual(e),
        important: true,
        multi: true,
      },
      {
        label: __('Remove from Recents'),
        icon: LucideClock,
        action: (entities) => {
          clearRecent.submit({
            entities,
          })
        },
        isEnabled: () => route.name == 'Recents',
        important: true,
        multi: true,
      },
      { divider: true, isEnabled: (e) => e.write },
      {
        label: __('Delete'),
        icon: LucideTrash,
        action: () => (dialog.value = 'remove'),
        isEnabled: (e) => e.write,
        important: true,
        multi: true,
        theme: 'red',
      },
    ]
  }
})

async function newLink() {
  if (!document.hasFocus()) return
  try {
    const text = await navigator.clipboard.readText()
    if (localStorage.getItem('prevClip') === text) return
    localStorage.setItem('prevClip', text)
    const url = new URL(text)
    if (url.host)
      toast({
        title: 'Link detected',
        text,
        buttons: [
          {
            label: 'Add',
            onClick: () => {
              dialog.value = 'l'
            },
          },
        ],
      })
  } catch { }
}

// JS doesn't allow direct reading of clipboard
if (settings.data?.auto_detect_links) {
  newLink()
  window.addEventListener('focus', newLink)
  window.addEventListener('copy', newLink)
}

const socket = inject('socket')
socket.on('list-add', ({ file }) => {
  if (
    file.folder === props.getEntities.params.entity_name &&
    !props.getEntities.data.find((k) => k.name === file.name)
  ) {
    props.getEntities.data.push(...prettyData([file]))
    props.getEntities.setData(props.getEntities.data)
  }
})
socket.on('list-update', ({ file }) => {
  if (file.folder !== props.getEntities.params.entity_name) return
  const index = props.getEntities.data.findIndex((k) => k.name == file.name)
  if (index !== -1)
    props.getEntities.data.splice(index, 1, ...prettyData([file]))
  props.getEntities.setData(props.getEntities.data)
})
socket.on('list-remove', ({ parent, entity_name }) => {
  if (parent !== props.getEntities.params.entity_name) return
  const index = props.getEntities.data.findIndex((k) => k.name == entity_name)
  if (index !== -1) props.getEntities.data.splice(index, 1)
  props.getEntities.setData(props.getEntities.data)
})
socket.on('client-rename', ({ entity_name, title }) => {
  const file = props.getEntities.data.find((k) => k.name === entity_name)
  file.file_name = title
})
</script>
<style>
.file-drag #drop-area {
  opacity: 0.5;
  padding-left: 0;
  padding-right: 0;
}

.file-drag #drop-area+p {
  display: block;
}
</style>
