<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
    :options="dialogOptions"
  >
    <template #body-content>
      <div class="flex items-center justify-start">
        <div class="text-base text-ink-gray-6">
          "{{
            props.entities.length > 1 ? "These items" : props.entities[0].title
          }}"
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
import { del } from "idb-keyval"
import { toast } from "@/utils/toasts.js"

import { mutate, getTrash } from "@/resources/files.js"
import { sortEntities } from "@/utils/files.js"
import { useTimeAgo } from "@vueuse/core"

import LucideRotateCcw from "~icons/lucide/rotate-ccw"
import { useRoute } from "vue-router"

const props = defineProps({
  entities: {
    type: Array,
    required: true,
  },
  clearAll: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits("success")
const dialogType = defineModel()
const open = ref(true)

const route = useRoute()

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
        "will be moved to Trash. <br/>Items in trash are deleted forever after 30 days.",
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
        " will be deleted - you can no longer access it.<br/><br/> <span class=font-semibold>This is an irreversible action.<b>",
      button: {
        label: "Delete — forever.",
        theme: "red",
        iconLeft: LucideTrash,
        variant: "solid",
      },
      toastMessage: `Deleted ${itemString}.`,
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
        onClick: updateResource.submit,
        loading: updateResource.loading,
        ...dialogData.value.button,
      },
    ],
  }
})

const updateResource = createResource({
  url: dialogData.value.url,
  makeParams: () => {
    open.value = ""
    return props.clearAll
      ? { clear_all: true }
      : {
          entity_names:
            typeof props.entities === "string"
              ? JSON.stringify([props.entities])
              : JSON.stringify(props.entities.map((entity) => entity.name)),
        }
  },
  onSuccess(data) {
    emit("success", data)
    updateResource.reset()
    props.entities.map((entity) => del(entity.name))
    if (dialogData.value.mutate) mutate(props.entities, props.dialogData.mutate)
    if (dialogData.value.onSuccess)
      dialogData.value.onSuccess(props.entities, data)
    toast({
      title: dialogData.value.toastMessage,
      position: "bottom-right",
      timeout: 2,
    })
  },
})
</script>
