<template>
  <TeamSelector
    v-model="chosenTeam"
    :disabled="Boolean(props.team)"
    none="home"
    class="mb-5"
  />
  <div
    v-if="!preview.data"
    class="text-sm text-center py-5"
  >
    Loading...
  </div>
  <div
    v-else-if="chosenTeam"
    class="text-base text-ink-gray-8"
  >
    <template v-if="preview.data.length">
      <div class="pb-2">
        You're adding {{ preview.data.length }}
        {{ preview.data.length == 1 ? "item" : "items" }}:
      </div>
      <div class="h-64 overflow-auto">
        <Tree
          v-for="item in tree"
          :key="item.label"
          :node="item"
          :node-key="item.label"
        >
          <template #icon="{ hasChildren, isCollapsed }">
            <template v-if="hasChildren">
              <LucideChevronDown
                v-if="!isCollapsed"
                class="size-3.5"
              />
              <LucideChevronRight
                v-else
                class="size-3.5"
              />
            </template>
            <div
              v-else
              class="ps-3.5"
            />
          </template>
          <template #label="{ node, hasChildren, isCollapsed }">
            <div class="text-base truncate pl-3.5 flex gap-2">
              <template v-if="hasChildren">
                <LucideFolderClosed
                  v-if="isCollapsed"
                  class="mr-1 size-4"
                />
                <LucideFolder
                  v-else
                  class="mr-1 size-4"
                />
              </template>
              <LucideFile
                v-else
                class="mr-1 size-4"
              />
              <div class="flex gap-1 select-none">
                {{ node.label }}
                <span
                  v-if="hasChildren"
                  class="text-ink-gray-5"
                  >({{ node.totalChildren }})</span
                >
              </div>
            </div>
          </template>
        </Tree>
      </div>
      <div class="font-semibold">
        <Alert
          type="info"
          class="mt-8"
        >
          If you already have files, make sure you have a backup.
        </Alert>
        <Button
          label="Confirm"
          class="w-full mt-8"
          variant="solid"
          :disabled="!preview.data?.length"
          @click="
            syncFromDisk.submit({ team: chosenTeam }),
              clearDialogs(),
              emitter.emit('showSettings', -1)
          "
        />
      </div>
    </template>
    <div
      v-else
      class="text-center"
    >
      No new files are available.
    </div>
  </div>
</template>
<script setup>
import { createResource, Tree } from "frappe-ui"
import Alert from "@/components/Alert.vue"
import { computed, ref, watch } from "vue"
import { useRoute } from "vue-router"
import { toast } from "@/utils/toasts"
import emitter from "@/emitter"
import TeamSelector from "./TeamSelector.vue"
import { clearDialogs } from "@/utils/dialogs"

const props = defineProps({
  team: { type: String, required: false },
})
const route = useRoute()
const chosenTeam = ref(props.team || route.params.team || "home")
function buildTree(items) {
  const root = {}

  for (const [path, meta] of items) {
    if (!path) continue
    const parts = path.split("/")
    let current = root

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (!current[part]) {
        current[part] = {
          label: part,
          children:
            i === parts.length - 1 && meta[2] !== "folder" ? undefined : {},
        }
      }
      if (current[part].children) current = current[part].children
    }
  }

  return convertToArray(root)
}

function convertToArray(nodeObj) {
  return Object.values(nodeObj).map((node) => {
    let children = undefined
    let totalChildren = 0

    if (node.children) {
      children = convertToArray(node.children)
      totalChildren = children.reduce(
        (sum, child) => sum + child.totalChildren + (!child.children ? 1 : 0),
        0
      )
    }

    return {
      label: node.label,
      children,
      totalChildren,
    }
  })
}

const tree = computed(() => preview.data && buildTree(preview.data))

const preview = createResource({
  url: "drive.api.scripts.sync_preview",
  cache: "preview",
})
watch(
  chosenTeam,
  (team) => {
    preview.data = null
    preview.submit({ team })
  },
  { immediate: true }
)
const syncFromDisk = createResource({
  url: "drive.api.scripts.sync_from_disk",
  beforeSubmit: () => {
    toast({
      icon: LucideFolderSync,
      title: "Starting syncing.",
      text: "We'll give you an update when it's done.",
    })
  },
  onSuccess: (d) => {
    toast({
      icon: LucideCloudCheck,
      title: "Successfully synced",
      text: d.length
        ? `Added ${d.length} item${d.length > 1 ? "s" : ""}`
        : "No new files were added.",
    })
    emitter.emit("refresh")
  },
  onError: () => {
    toast({
      icon: LucideCloudAlert,
      title: "There was an error.",
      text: "Is there an issue with your configuration?",
    })
  },
})
</script>
