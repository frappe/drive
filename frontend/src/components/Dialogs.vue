<template>
  <!-- New item dialogs -->
  <NewFolderDialog
    v-if="dialog === 'f'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="addToList"
  />
  <NewLinkDialog
    v-if="dialog === 'l'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="addToList"
  />
  <!-- Mutation dialog -->
  <RenameDialog
    v-if="dialog === 'rn'"
    v-model="dialog"
    :entity="selections[0]"
    @success="
      ({ name, title }) => {
        if (props.getEntities)
          props.getEntities.data.find((k) => k.name === name).title = title
        resetDialog()
        // Handle breadcrumbs
        let l = store.state.breadcrumbs[store.state.breadcrumbs.length - 1]
        if (l.label === selections[0].title) {
          l.label = title
          setTitle(title)
        }
      }
    "
  />
  <ShareDialog
    v-if="dialog === 's'"
    v-model="dialog"
    :selections="selections[0]"
  />

  <!-- Deletion dialogs -->
  <GeneralDialog
    v-if="dialog === 'remove'"
    v-model="dialog"
    :entities="selections"
    :for="'remove'"
    @success="removeFromList(selections)"
  />
  <GeneralDialog
    v-if="dialog === 'restore'"
    v-model="dialog"
    :entities="selections"
    :for="'restore'"
    @success="removeFromList(selections)"
  />

  <MoveDialog
    v-if="dialog === 'm'"
    v-model="dialog"
    :entities="selections"
    @success="removeFromList(selections)"
  />
  <DeleteDialog
    v-if="dialog === 'd'"
    v-model="dialog"
    :entities="selections"
    @success="removeFromList(selections)"
  />
  <CTADeleteDialog
    v-if="dialog === 'cta'"
    v-model="dialog"
    @success="resetDialog"
  />
</template>
<script setup>
import NewFolderDialog from "@/components/NewFolderDialog.vue"
import NewLinkDialog from "@/components/NewLinkDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"
import GeneralDialog from "@/components/GeneralDialog.vue"
import DeleteDialog from "@/components/DeleteDialog.vue"
import CTADeleteDialog from "@/components/CTADeleteDialog.vue"
import MoveDialog from "@/components/MoveDialog.vue"
import emitter from "@/emitter"
import { useStore } from "vuex"

const dialog = defineModel(String)
const store = useStore()

const props = defineProps({
  getEntities: Object,
  selections: Array,
})
const resetDialog = () => (dialog.value = null)

emitter.on("showCTADelete", () => (dialog.value = "cta"))
emitter.on("showShareDialog", () => (dialog.value = "s"))
emitter.on("newFolder", () => (dialog.value = "f"))
emitter.on("rename", () => (dialog.value = "rn"))
emitter.on("newLink", () => (dialog.value = "l"))

const setTitle = (title) => (document.title = title)

function addToList(data) {
  props.getEntities.data.push(data)
  props.getEntities.setData(props.getEntities.data)
  props.getEntities.fetch()
  resetDialog()
}

function removeFromList(entities) {
  const names = entities.map((o) => o.name)
  props.getEntities.setData(
    props.getEntities.data.filter(({ name }) => !names.includes(name))
  )
  props.getEntities.fetch()
  resetDialog()
}
</script>
