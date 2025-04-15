<template>
  <NewFolderDialog
    v-if="dialog === 'f'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="
      (data) => {
        handleListMutate({ new: true, data })
        getEntities && getEntities.fetch()
        resetDialog()
      }
    "
  />
  <NewLinkDialog
    v-if="dialog === 'l'"
    v-model="dialog"
    :parent="$route.params.entityName"
    @success="
      (data) => {
        handleListMutate({ new: true, data })
        getEntities && getEntities.fetch()
        resetDialog()
      }
    "
  />
  <RenameDialog
    v-if="dialog === 'rn'"
    v-model="dialog"
    :entity="selections[0]"
    @success="
      (data) => {
        let l = store.state.breadcrumbs[store.state.breadcrumbs.length - 1]
        if (l.label === selections[0].title) {
          l.label = data.title
          setTitle(data.title)
        }
        handleListMutate({ data })
        resetDialog()
      }
    "
  />
  <GeneralDialog
    v-if="dialog === 'remove'"
    v-model="dialog"
    :entities="selections"
    :for="'remove'"
    @success="resetDialog"
  />
  <GeneralDialog
    v-if="dialog === 'restore'"
    v-model="dialog"
    :entities="selections"
    :for="'restore'"
    @success="resetDialog"
  />
  <ShareDialog
    v-if="dialog === 's'"
    v-model="dialog"
    :selections="selections[0]"
  />
  <MoveDialog
    v-if="dialog === 'm'"
    v-model="dialog"
    :entities="selections"
    @success="resetDialog(), mutate({ delete: true, data: selections })"
  />
  <DeleteDialog
    v-if="dialog === 'd'"
    v-model="dialog"
    :entities="selections"
    @success="resetDialog(), mutate({ delete: true, data: selections })"
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
  handleListMutate: { type: Function, default: () => {} },
  selections: Array,
})
const resetDialog = () => (dialog.value = null)

emitter.on("showCTADelete", () => (dialog.value = "cta"))
emitter.on("showShareDialog", () => (dialog.value = "s"))
emitter.on("newFolder", () => (dialog.value = "f"))
emitter.on("rename", () => (dialog.value = "rn"))
emitter.on("newLink", () => (dialog.value = "l"))

const mutate = (data) => {
  data.data.map((k) => props.handleListMutate({ ...data, data: k }))
  resetDialog()
}

const setTitle = (title) => (document.title = title)
</script>
