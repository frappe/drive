<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
    :options="dialogOptions"
  >
    <template #body-content>
      <div class="flex items-center justify-start">
        <div class="text-base text-ink-gray-6">
          <template v-if="props.entities.length"
            >"{{
              props.entities.length > 1
                ? "These items"
                : props.entities[0].title
            }}"
          </template>
          <span v-html="dialogData.message" />
        </div>
      </div>
      <ErrorMessage
        class="my-1 text-center"
        :message="updateResource.error"
      />
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed } from "vue"
import { createResource, Dialog, ErrorMessage } from "frappe-ui"
import { toast } from "@/utils/toasts.js"
import { useTimeAgo } from "@vueuse/core"

import {
  mutate,
  getTrash,
  toggleFav,
  clearRecent,
  clearTrash,
} from "@/resources/files.js"
import { sortEntities } from "@/utils/files.js"

import LucideRotateCcw from "~icons/lucide/rotate-ccw"
import {} from "@/resources/files"

const props = defineProps({
  entities: {
    type: Array,
    required: true,
  },
})
const emit = defineEmits("success")
const dialogType = defineModel()
const open = ref(true)

const dialogData = computed(() => {
  const itemString =
    props.entities.length === 1 ? "an item" : `${props.entities.length} items`
  const MAP = {
    restore: {
      title: `Restore ${itemString}`,
      message: `will be restored to ${
        props.entities.length === 1
          ? "its original location"
          : "their original locations"
      }.`,
      url: "drive.api.files.remove_or_restore",
      onSuccess: () => {
        getTrash.setData((d) =>
          d.filter((k) => !e.map((l) => l.name).includes(k.name))
        )
      },
      button: {
        variant: "solid",
        label: "Restore",
        iconLeft: LucideRotateCcw,
      },
      toastMessage: `Restored ${itemString}.`,
    },
    remove: {
      title: `Move ${itemString} to Trash`,
      message:
        "will be moved to Trash.<br/><br/> Items in trash are deleted forever after 30 days.",
      url: "drive.api.files.remove_or_restore",
      button: {
        label: "Move to Trash",
        theme: "red",
        variant: "subtle",
      },
      onSuccess: (e) => {
        getTrash.setData(
          sortEntities([
            ...getTrash.data,
            ...e.map((k) => {
              k.modified = Date()
              k.relativeModified = useTimeAgo(k.modified)
              return k
            }),
          ])
        )
      },
      toastMessage: `Moved ${itemString} to Trash.`,
    },
    d: {
      title: `Delete ${itemString}`,
      url: "drive.api.files.delete_entities",
      message:
        " will be deleted - you can no longer access it.<br/><br/> <span class=font-semibold>This is an irreversible action.<span>",
      button: {
        label: "Delete — forever.",
        theme: "red",
        iconLeft: LucideTrash,
        variant: "solid",
      },
      toastMessage: `Deleted ${itemString}.`,
    },
    "cta-recents": {
      title: "Are you sure?",
      message: "All your recently viewed files will be cleared.",
      button: { label: "Clear" },
      resource: clearRecent,
    },
    "cta-favourites": {
      title: "Are you sure?",
      message: "All your favourite items will be cleared.",
      button: { label: "Clear" },
      resource: toggleFav,
    },
    "cta-trash": {
      title: "Clear your Trash",
      message:
        "All items in your Trash will be deleted forever. <br/><br/> <span class=font-semibold>This is an irreversible process.</span>",
      button: { label: "Delete", variant: "solid", iconLeft: LucideTrash },
      resource: clearTrash,
    },
  }
  return MAP[dialogType.value]
})

const dialogOptions = computed(() => {
  return {
    title: dialogData.value.title,
    size: "sm",
    actions: [
      {
        onClick: async () => {
          if (dialogData.value.resource) {
            open.value = false
            await dialogData.value.resource.submit()
            emit("success")
          } else updateResource.submit()
        },
        loading: (dialogData.value.resource || updateResource).loading,
        ...dialogData.value.button,
      },
    ],
  }
})

const updateResource = createResource({
  url: dialogData.value.url,
  makeParams: () => {
    open.value = ""
    return {
      entity_names:
        typeof props.entities === "string"
          ? JSON.stringify([props.entities])
          : JSON.stringify(props.entities.map((entity) => entity.name)),
    }
  },
  onSuccess(data) {
    emit("success", data)
    updateResource.reset()
    if (dialogData.value.mutate) mutate(props.entities, props.dialogData.mutate)
    if (dialogData.value.onSuccess)
      dialogData.value.onSuccess(props.entities, data)
    toast(dialogData.value.toastMessage)
  },
})
</script>
