<template>
  <nav
    v-if="store.state.breadcrumbs?.length"
    id="navbar"
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-surface-base border-b px-5 py-2.5 h-12 flex justify-between"
  >
    <slot name="breadcrumbs">
      <Breadcrumbs :items="store.state.breadcrumbs" class="select-none truncate max-w-[80%]">
        <template #prefix="{ item, index }">
          <LoadingIndicator v-if="item.loading" width="20" scale="70" />
        </template>
      </Breadcrumbs>
    </slot>

    <div class="flex gap-2">
      <div id="navbar-content" class="flex items-center">
        <div class="icon mr-2">
          <LucideGlobe2 v-if="rootEntity?.share_count === -2" class="size-4" />
          <LucideBuilding2 v-else-if="rootEntity?.share_count === -1" class="size-4" />
          <LucideUsers v-else-if="rootEntity?.share_count > 0" class="size-4" />
        </div>
      </div>

      <LucideStar
        v-if="rootEntity?.is_favourite"
        width="16"
        height="16"
        class="my-auto text-ink-amber-6 stroke-current fill-current"
      />
      <template v-if="!isLoggedIn && !inIframe">
        <Button variant="outline" @click="redirectLogin">Sign In</Button>
        <Button
          class="hidden md:block"
          variant="solid"
          label="Try out Drive"
          @click="open('https://frappecloud.com/dashboard/signup?product=drive')"
        />
      </template>
      <Dropdown
        v-else-if="defaultActions"
        :options="defaultActions"
        placement="right"
        :button="{
          variant: 'ghost',
          icon: LucideMoreHorizontal,
        }"
      />
      <Dropdown
        v-if="
          ['Folder', 'Home', 'Team'].includes($route.name) &&
          isLoggedIn &&
          // Assume upload to remove flash
          props.rootResource?.data?.upload !== false
        "
        :button="{
          variant: 'solid',
          id: 'create-button',
          label: 'Create',
          iconLeft: h(LucidePlus, { class: 'size-4' }),
        }"
        :options="newEntityOptions"
        placement="right"
      />
      <Button
        v-else-if="$route.name === 'Documents' || $route.name === 'Presentations'"
        id="create-button"
        label="Create"
        variant="solid"
        :icon-left="h(LucidePlus, { class: 'size-4' })"
        @click="newExternal($route.name === 'Documents' ? 'Document' : 'Presentation')"
      />
      <Button
        v-if="button"
        :disabled="!button.entities.data?.length"
        :theme="button.theme || 'gray'"
        @click="dialog = 'cta-' + $route.name.toLowerCase()"
      >
        <template #prefix>
          <component :is="button.icon" class="size-4" />
        </template>
        {{ button.label }}
      </Button>
    </div>
    <Dialogs
      v-model="dialog"
      :entities="entities.length ? entities : rootEntity ? [rootEntity] : []"
    />
  </nav>
</template>
<script setup>
import { Button, Breadcrumbs, LoadingIndicator, Dropdown } from 'frappe-ui'
import { useStore } from 'vuex'
import emitter from '@/emitter'
import { ref, computed, inject, h } from 'vue'
import { entitiesDownload } from '@/utils/download'
import { getRecents, getTrash, toggleFav } from '@/resources/files'
import { apps } from '@/resources/permissions'
import { useRoute } from 'vue-router'
import {
  newExternal,
  dynamicList,
  isManaged,
  isAttachmentRef,
  isSiteFile,
  isVirtual,
} from '@/utils/files'
import { getFileLink } from '@/ui/drive/js/utils'

import LucideClock from '~icons/lucide/clock'
import LucideHome from '~icons/lucide/home'
import LucideTrash from '~icons/lucide/trash'
import LucideUsers from '~icons/lucide/users'
import LucideBuilding2 from '~icons/lucide/building-2'
import LucideStar from '~icons/lucide/star'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import LucideShare2 from '~icons/lucide/share-2'
import LucideDownload from '~icons/lucide/download'
import LucidePlus from '~icons/lucide/plus'
import LucideLink from '~icons/lucide/link'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideCornerLeftUp from '~icons/lucide/corner-left-up'
import LucideMonitorCog from '~icons/lucide/monitor-cog'
import LucideSquarePen from '~icons/lucide/square-pen'
import LucideInfo from '~icons/lucide/info'
import LucideFileUp from '~icons/lucide/file-up'
import LucideFolderUp from '~icons/lucide/folder-up'
import LucideFilePlus2 from '~icons/lucide/file-plus-2'
import LucideGalleryVerticalEnd from '~icons/lucide/gallery-vertical-end'
import LucideFolderPlus from '~icons/lucide/folder-plus'

const store = useStore()
const route = useRoute()
const open = (url) => {
  window.open(url, '_blank')
}

const props = defineProps({
  rootResource: Object,
  actions: { type: Array, required: false },
  // Used to pass into dialogs
  entities: {
    type: Array,
    default: () => [],
  },
})

const isLoggedIn = computed(() => store.getters.isLoggedIn)
const dialog = inject('dialog', ref(''))
const rootEntity = computed(() => props.rootResource?.data?.file_name && props.rootResource?.data)

const defaultActions = computed(() => {
  if (!rootEntity.value?.file_name) return
  let actions = []
  if (props.actions) {
    if (props.actions[0] === 'extend') actions = props.actions.slice(1)
    else return props.actions
  }
  return [
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __('Open in Desk'),
          icon: LucideMonitorCog,
          onClick: () => window.open('/desk/file/' + rootEntity.value.name, '_blank'),
          isEnabled: () => isSiteFile(rootEntity.value) && store.state.user.systemUser,
        },
        {
          label: __('Go to original'),
          icon: LucideCornerLeftUp,
          onClick: () => {
            window.open(
              '/api/method/drive.api.files.redirect_to_original?file_id=' + rootEntity.value.name,
              '_blank'
            )
          },
          isEnabled: () => isAttachmentRef(rootEntity.value),
        },
        {
          label: __('Download'),
          icon: LucideDownload,
          isEnabled: () =>
            !isVirtual(rootEntity.value) &&
            !['Link', 'Presentation', 'Document'].includes(rootEntity.value.file_type),
          onClick: () => entitiesDownload([rootEntity.value]),
        },
        {
          label: __('Copy Link'),
          icon: LucideLink,
          onClick: () => getFileLink(rootEntity.value),
        },
        {
          label: __('Show Info'),
          icon: LucideInfo,
          onClick: () => (dialog.value = 'i'),
          isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
        },
      ],
    },
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __('Share'),
          icon: LucideShare2,
          onClick: () => {
            dialog.value = 's'
          },
          isEnabled: () => rootEntity.value.share && isManaged(rootEntity.value),
        },
        {
          label: __('Rename'),
          icon: LucideSquarePen,
          onClick: () => (dialog.value = 'rn'),
          isEnabled: () => rootEntity.value.write && isManaged(rootEntity.value),
        },
        {
          label: __('Move'),
          icon: LucideArrowLeftRight,
          onClick: () => (dialog.value = 'm'),
          isEnabled: () => rootEntity.value.write && isManaged(rootEntity.value),
        },
        {
          label: __('Favourite'),
          icon: LucideStar,
          onClick: () => {
            rootEntity.value.is_favourite = true
            toggleFav.submit({
              entities: [{ name: rootEntity.value.name, is_favourite: false }],
            })
          },
          isEnabled: () => !rootEntity.value.is_favourite,
        },
        {
          label: __('Unfavourite'),
          icon: LucideStar,
          color: 'text-ink-amber-6 stroke-current fill-current',
          onClick: () => {
            rootEntity.value.is_favourite = false
            toggleFav.submit({
              entities: [{ name: rootEntity.value.name, is_favourite: false }],
            })
          },
          isEnabled: () => rootEntity.value.is_favourite,
        },
      ],
    },
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: LucideTrash,
          onClick: () => (dialog.value = 'remove'),
          isEnabled: () => rootEntity.value.write,
          theme: 'red',
        },
      ],
    },
    ...actions,
  ].map((k) => {
    return { ...k, items: k.items.filter((l) => !l.isEnabled || l.isEnabled()) }
  })
})
const isPrivate = computed(() => (store.state.breadcrumbs[0]?.name === 'Home' ? 1 : 0))

// Functions

// Constants
const possibleButtons = [
  {
    route: 'Recents',
    label: __('Clear'),
    icon: LucideClock,
    entities: getRecents,
  },
  {
    route: 'Trash',
    label: __('Empty'),
    icon: LucideTrash,
    entities: getTrash,
    theme: 'red',
  },
]
const button = computed(() => possibleButtons.find((k) => k.route == route.name))

const newEntityOptions = computed(() => [
  {
    group: 'Create',
    items: dynamicList([
      {
        label: 'Document',
        icon: LucideFilePlus2,
        onClick: () => newExternal('Document'),
      },
      {
        label: 'Presentation',
        icon: LucideGalleryVerticalEnd,
        onClick: () => newExternal('Presentation'),
        cond: isPrivate.value && apps.data?.find?.((k) => k.name === 'slides'),
      },
      {
        label: 'Folder',
        icon: LucideFolderPlus,
        onClick: () => (dialog.value = 'f'),
      },
      {
        label: 'Link',
        icon: LucideLink,
        onClick: () => (dialog.value = 'l'),
      },
    ]),
  },
  {
    group: 'Upload',
    items: [
      {
        label: 'Upload File',
        icon: LucideFileUp,
        onClick: () => emitter.emit('uploadFile'),
      },
      {
        label: 'Upload Folder',
        icon: LucideFolderUp,
        onClick: () => emitter.emit('uploadFolder'),
      },
    ],
  },
])

const inIframe = inject('inIframe')
const redirectLogin = () => {
  window.location.href =
    '/login?redirect-to=' + encodeURIComponent('/drive' + route.path)
}
</script>
