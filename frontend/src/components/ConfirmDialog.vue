<template>
  <Dialog
    v-model="open"
    :options="dialogOptions"
    @close="dialogType = ''"
  >
    <template #body-content>
      <div class="flex items-center justify-start">
        <div class="text-base text-ink-gray-6">
          <template v-if="props.entities.length">
            {{
              props.entities.length > 1
                ? __("These items ")
                : `"${props.entities[0].title}" `
            }}
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
import { createResource, Dialog, ErrorMessage, toast } from "frappe-ui"
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
const emit = defineEmits(["success"])
const dialogType = defineModel()
const open = ref(true)

const dialogData = computed(() => {
  const itemString =
    props.entities.length === 1 ? __("an item") : __("{0} items").replace("{0}", props.entities.length)
  const MAP = {
    restore: {
      title: __("Restore {0}").replace("{0}", itemString),
      message: props.entities.length === 1
        ? __("will be restored to its original location.")
        : __("will be restored to their original locations."),
      url: "drive.api.files.remove_or_restore",
      onSuccess: () => {
        getTrash.setData((d) =>
          d.filter((k) => !props.entities.map((l) => l.name).includes(k.name))
        )
      },
      button: {
        variant: "solid",
        label: __("Restore"),
        iconLeft: LucideRotateCcw,
      },
      toastMessage: __("Restored {0}.").replace("{0}", itemString),
    },
    remove: {
      title: __("Move {0} to Trash").replace("{0}", itemString),
      message:
        __("will be moved to Trash.") + "<br/><br/>" + __("Items in trash are deleted forever after 30 days."),
      url: "drive.api.files.remove_or_restore",
      button: {
        label: __("Move to Trash"),
        theme: "red",
        variant: "subtle",
      },
      onSuccess: () => {
        getTrash.setData(
          sortEntities([
            ...getTrash.data,
            ...props.entities.map((k) => {
              k.modified = Date()
              k.relativeModified = useTimeAgo(k.modified)
              return k
            }),
          ])
        )
      },
      toastMessage: __("Moved {0} to Trash.").replace("{0}", itemString),
    },
    d: {
      title: __("Delete {0}").replace("{0}", itemString),
      url: "drive.api.files.delete_entities",
      message:
        __("will be deleted - you can no longer access it.") + "<br/><br/> <span class=font-semibold>" + __("This is an irreversible action.") + "<span>",
      button: {
        label: __("Delete — forever."),
        theme: "red",
        iconLeft: LucideTrash,
        variant: "solid",
      },
      toastMessage: __("Deleted {0}.").replace("{0}", itemString),
    },
    "cta-recents": {
      title: __("Are you sure?"),
      message: __("All your recently viewed files will be cleared."),
      button: { label: __("Clear") },
      resource: clearRecent,
    },
    "cta-favourites": {
      title: __("Are you sure?"),
      message: __("All your favourite items will be cleared."),
      button: { label: __("Clear") },
      resource: toggleFav,
    },
    "cta-trash": {
      title: __("Clear your Trash"),
      message:
        __("All items in your Trash will be deleted forever.") + " <br/><br/> <span class=font-semibold>" + __("This is an irreversible process.") + "</span>",
      button: { label: __("Delete"), variant: "solid", iconLeft: LucideTrash },
      resource: clearTrash,
    },
  }
  return MAP[dialogType.value]
})

const loading = computed(
  () => (dialogData.value.resource || updateResource).loading
)
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
        ...dialogData.value.button,
        disabled: loading.value,
        // loading: loading.value,
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
    toast.success(dialogData.value.toastMessage)
  },
})
</script>
