<template>
  <!-- New dialogs -->
  <NewFolderDialog
    v-if="dialog === 'f'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="(data) => addToList(data, 'Folder')"
  />
  <NewLinkDialog
    v-else-if="dialog === 'l'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="(data) => addToList(data, 'Link')"
  />

  <!-- Mutation dialogs -->
  <RenameDialog
    v-if="dialog === 'rn'"
    v-model="dialog"
    :entity="entities[0]"
    @success="
      ({ name, title }) => {
        if (entities[0] !== rootResource?.data && props.getEntities)
          props.getEntities.data.find((k) => k.name === name).title = title
        resetDialog()
      }
    "
  />
  <ShareDialog
    v-if="dialog === 's'"
    v-model="dialog"
    :entity="entities[0]"
    @success="getEntities.fetch(getEntities.params)"
  />
  <MoveDialog
    v-if="dialog === 'm'"
    v-model="dialog"
    :entities="entities"
    @success="removeFromList(entities)"
  />
  <InfoPopup
    v-if="dialog === 'i'"
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
import { ref, watch } from "vue"
import { useStore } from "vuex"
import { useTimeAgo } from "@vueuse/core"
import { sortEntities, openEntity } from "@/utils/files"

import emitter from "@/emitter"

import NewFolderDialog from "@/components/NewFolderDialog.vue"
import NewLinkDialog from "@/components/NewLinkDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"
import ConfirmDialog from "@/components/ConfirmDialog.vue"
import MoveDialog from "@/components/MoveDialog.vue"

const props = defineProps({
  rootResource: Object,
  entities: Array,
  getEntities: { type: Object, default: null },
})
const store = useStore()

const dialog = defineModel(String)
const open = ref(false)
watch(dialog, (val) => {
  if (val) open.value = true
})

const resetDialog = () => (dialog.value = "")

emitter.on("showShareDialog", () => (dialog.value = "s"))
emitter.on("newFolder", () => {
  console.log("emittted")
  dialog.value = "f"
})
emitter.on("rename", () => (dialog.value = "rn"))
emitter.on("remove", () => (dialog.value = "remove"))
emitter.on("move", () => (dialog.value = "m"))
emitter.on("newLink", () => (dialog.value = "l"))

function addToList(data, file_type) {
  if (!props.getEntities) return
  data = {
    ...data,
    modified: Date(),
    file_type,
    share_count: 0,
    read: 1,
    write: 1,
    share: 1,
    comment: 1,
  }

  data.relativeModified = useTimeAgo(data.modified)

  const newData = [...props.getEntities.data, data]
  sortEntities(newData, store.state.sortOrder)
  props.getEntities.setData(newData)
  resetDialog()
  dialog.value = ""
}

function removeFromList(entities, move = true) {
  // Hack (that breaks for some reason)
  if (!props.getEntities?.data && props.rootResource) {
    if (move) {
      store.state.breadcrumbs.splice(1)
      store.state.breadcrumbs.push({ loading: true })
      setTimeout(() => props.rootResource.fetch(), 1000)
    } else {
      openEntity(null, {
        team: props.rootResource.data.team,
        name: props.rootResource.data.parent_entity,
        is_group: true,
      })
    }
  } else {
    const names = entities.map((o) => o.name)
    props.getEntities.setData(
      props.getEntities.data.filter(({ name }) => !names.includes(name))
    )
  }
  resetDialog()
}
</script>
