<template>
  <!-- New dialogs -->
  <NewFolderDialog
    v-if="dialog === 'f'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="(data) => addToList(data, 'Folder')"
  />
  <NewPresentationDialog
    v-else-if="dialog === 'p'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="(data) => addToList(data, 'Presentation')"
  />
  <NewLinkDialog
    v-else-if="dialog === 'l'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="(data) => addToList(data, 'Link')"
  />

  <!-- Mutation dialogs -->
  <RenameDialog
    v-else-if="dialog === 'rn'"
    v-model="dialog"
    :entity="entities[0]"
    @success="
      ({ name, title }) => {
        const el = listResource?.data?.find?.((k) => k.name === name)
        if (el) el.title = title
        resetDialog()
      }
    "
  />
  <ShareDialog
    v-else-if="dialog === 's'"
    v-model="dialog"
    :entity="entities[0]"
    @success="
      () => {
        resource.fetch(resource.params)
      }
    "
  />
  <MoveDialog
    v-else-if="dialog === 'm'"
    v-model="dialog"
    :entities="entities"
    @success="removeFromList(entities)"
    @complete="entity_open && resource.fetch(resource.params)"
  />
  <InfoPopup
    v-else-if="dialog === 'i'"
    v-model="dialog"
    :entity="entities[0]"
  />

  <!-- Confirmation dialogs -->
  <ConfirmDialog
    v-if="
      [
        'remove',
        'restore',
        'd',
        'cta-favourites',
        'cta-recents',
        'cta-trash',
      ].includes(dialog)
    "
    v-model="dialog"
    :entities="entities"
    @success="
      dialog === 'cta'
        ? resetDialog
        : removeFromList(entities, dialog === 'restore')
    "
  />
</template>
<script setup>
import { ref, watch, computed } from "vue"
import { useStore } from "vuex"
import { useTimeAgo } from "@vueuse/core"
import { openEntity } from "@/utils/files"

import emitter from "@/emitter"

import NewFolderDialog from "@/components/NewFolderDialog.vue"
import NewPresentationDialog from "@/components/NewPresentationDialog.vue"
import NewLinkDialog from "@/components/NewLinkDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import { ShareDialog } from "frappe-ui/drive"
import ConfirmDialog from "@/components/ConfirmDialog.vue"
import MoveDialog from "@/components/MoveDialog.vue"

const props = defineProps({
  entities: Array,
})
const store = useStore()
const listResource = computed(() => store.state.listResource)
const resource = computed(() =>
  store.state.currentResource && Object.keys(store.state.currentResource).length
    ? store.state.currentResource
    : listResource.value
)
const entity_open = computed(
  () =>
    resource.value.data?.name &&
    props.entities[0]?.name === resource.value.data?.name
)

const dialog = defineModel(String)
const open = ref(false)
watch(dialog, (val) => {
  if (val) open.value = true
})

const resetDialog = () => (dialog.value = "")

emitter.on("share", () => (dialog.value = "s"))
emitter.on("newFolder", () => (dialog.value = "f"))
emitter.on("rename", () => (dialog.value = "rn"))
emitter.on("remove", () => (dialog.value = "remove"))
emitter.on("move", () => (dialog.value = "m"))
emitter.on("newLink", () => (dialog.value = "l"))

function addToList(data, file_type) {
  resetDialog()
  if (!listResource.value) return
  const now = Date()
  data = {
    ...data,
    modified: now,
    file_type,
    share_count: 0,
    read: 1,
    write: 1,
    share: 1,
    comment: 1,
    relativeModified: useTimeAgo(now),
  }
  listResource.value.data.push(data)
}

function removeFromList(entities, move = true) {
  if (entity_open.value) {
    if (move) {
      store.state.breadcrumbs.splice(1)
      store.state.breadcrumbs.push({ loading: true })
    } else {
      resetDialog()
      listResource.value.setData(
        listResource.value.data.filter(
          ({ name }) => name !== resource.value.data.name
        )
      )
      openEntity({
        is_group: 1,
        name: resource.value.data.parent_entity,
        breadcrumbs: resource.value.data.breadcrumbs.slice(0, -1),
      })
    }
  } else {
    resetDialog()
    if (listResource.value) {
      const names = entities.map((o) => o.name)
      listResource.value.setData(
        listResource.value.data.filter(({ name }) => !names.includes(name))
      )
    }
  }
}
</script>
