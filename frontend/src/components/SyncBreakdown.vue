<template>
  <TeamSelector
    :none="true"
    v-model="chosenTeam"
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
    You're adding {{ preview.data.length }}
    {{ preview.data.length == 1 ? "item" : "items" }}:
    <div class="pt-3 h-64 overflow-auto">
      <Tree
        v-for="item in tree"
        :node="item"
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
            <div class="flex gap-1">
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
        Make sure you have a backup before proceeding.
      </Alert>
    </div>
  </div>
  <Button
    label="Confirm"
    class="w-full mt-8"
    variant="solid"
    :disabled="!preview.data?.length"
    @click="syncFromDisk.submit"
  />
</template>
<script setup>
import { createResource, Tree } from "frappe-ui"
import Alert from "@/components/Alert.vue"
import { computed, ref, watch } from "vue"
import { toast } from "@/utils/toasts"
import emitter from "@/emitter"
import TeamSelector from "./TeamSelector.vue"

const props = defineProps({ team: String })
const chosenTeam = ref("all")
function buildTree(items) {
  const root = {}

  for (const [path, meta] of items) {
    if (!path) continue
    const parts = path.split("/")
    let current = root

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (!current[part]) {
        console.log(part, meta)
        current[part] = {
          label: part,
          children:
            i === parts.length - 1 && meta[2] !== "folder" ? undefined : {},
        }
      }
      current = current[part].children
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
        (sum, child) => sum + 1 + child.totalChildren,
        0
      )
    }

    return {
      label: node.label,
      children: children,
      totalChildren: totalChildren,
    }
  })
}

const tree = computed(() => preview.data && buildTree(preview.data))

const preview = createResource({
  url: "drive.api.scripts.sync_preview",
  cache: ["preview", chosenTeam],
})
watch(chosenTeam, (team) => preview.submit({ team }), { immediate: true })

const syncFromDisk = createResource({
  url: "drive.api.scripts.sync_from_disk",
  params: { team: props.team },
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
