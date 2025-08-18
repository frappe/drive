<template>
  <div
    class="flex flex-col items-start fixed bottom-0 right-0 w-full m-5 sm:w-96 z-10 rounded-2xl overflow-hidden shadow-2xl 500 bg-surface-white p-4"
  >
    <div
      class="flex items-center justify-between w-full mb-4 pr-1.5"
      :class="[collapsed ? 'cursor-pointer' : '']"
      @click="collapsed = false"
    >
      <div
        v-if="uploadsInProgress.length > 0"
        class="font-medium truncate text-lg"
      >
        Uploading {{ uploadsInProgress.length }}
        {{ uploadsInProgress.length == 1 ? "file" : "files" }}
      </div>
      <div
        v-else-if="uploadsCompleted.length > 0"
        class="font-medium truncate text-lg"
      >
        {{ uploadsCompleted.length }}
        {{ uploadsCompleted.length == 1 ? "upload" : "uploads" }} complete
      </div>
      <div
        v-else-if="uploadsFailed.length > 0"
        class="font-medium truncate text-lg"
      >
        {{ uploadsFailed.length }}
        {{ uploadsFailed.length == 1 ? "upload" : "uploads" }} failed
      </div>
      <div class="ml-auto flex items-center gap-4">
        <button
          v-if="!collapsed"
          class="focus:outline-none"
          @click.stop="toggleCollapsed"
        >
          <LucideMinus class="size-4 text-ink-gray-8" />
        </button>
        <button
          class="focus:outline-none"
          @click="close"
        >
          <LucideX class="size-4 text-ink-gray-8" />
        </button>
      </div>
    </div>
    <div
      class="bg-surface-gray-2 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1 mb-2"
    >
      <TabButtons
        v-model="currentTab"
        :buttons="
          uploadsFailed.length > 0
            ? [
                { value: 1, label: 'In Progress' },
                { value: 2, label: 'Completed' },
                { value: 3, label: 'Failed' },
              ]
            : [
                { value: 1, label: 'In Progress' },
                { value: 2, label: 'Completed' },
              ]
        "
      />
    </div>
    <div
      v-if="!collapsed"
      class="max-h-64 overflow-y-auto bg-surface-white w-full"
    >
      <span
        v-if="!currentTabGetter().length"
        class="px-1.5 text-base font-medium text-ink-gray-8"
        >{{ emptyMessage }}</span
      >
      <div
        v-for="(upload, index) in currentTabGetter()"
        :key="upload.uuid"
        class="cursor-pointer truncate hover:bg-surface-menu-bar rounded px-1 group"
        @mouseover="hoverIndex = index"
        @mouseout="hoverIndex = null"
      >
        <div
          class="flex items-center gap-3 py-2 pr-[3px]"
          @click="openFile(upload)"
        >
          <div class="flex items-center justify-between w-full">
            <div class="flex justify-start items-center w-full max-w-[80%]">
              <LucideFile class="w-5 mr-2" />
              <p class="truncate text-sm leading-6 col-span-1 row-span-1">
                {{ upload.name }}
              </p>
            </div>
            <Button
              variant="ghost"
              :icon="upload.error ? LucideInfo : LucideFolderOpenDot"
              v-if="upload.completed"
            />
            <ProgressRing
              v-if="!upload.completed && !upload.error"
              :radius="13"
              :progress="Math.min(upload.progress, 95)"
            />
            <!-- <Button
              variant="ghost"
              :icon="LucideX"
              class="rounded-full hover:bg-surface-red-4"
              @click="emitter.emit('cancelUpload', upload.uuid)"
            /> -->
          </div>
        </div>
      </div>
    </div>
    <Dialog
      v-if="showErrorDialog"
      v-model="showErrorDialog"
      :options="{
        title: 'Upload failed',
        message: selectedUpload.error,
        size: 'sm',
        actions: [
          {
            label: 'OK',
            variant: 'solid',
            onClick: () => {
              showErrorDialog = false
            },
          },
        ],
      }"
    />
  </div>
</template>
<script setup>
import { Dialog, TabButtons } from "frappe-ui"
import ProgressRing from "@/components/ProgressRing.vue"
import LucideInfo from "~icons/lucide/info"
import LucideFolderOpenDot from "~icons/lucide/folder-open-dot"
import LucideX from "~icons/lucide/x"
import { useStore } from "vuex"
import { useRouter } from "vue-router"
import { ref, computed } from "vue"

const collapsed = ref(false)
const showErrorDialog = ref(false)
const hoverIndex = ref(null)
const selectedUpload = ref(null)
const currentTab = ref(1)
const emptyMessage = ref("No uploads in progress")

const store = useStore()
const router = useRouter()

const currentTabGetter = () => {
  switch (currentTab.value) {
    case 1:
      emptyMessage.value = "No uploads in progress"
      return uploadsInProgress.value
    case 2:
      emptyMessage.value = "No uploads completed"
      return uploadsCompleted.value
    case 3:
      emptyMessage.value = "No failed uploads"
      return uploadsFailed.value
    default:
      emptyMessage.value = "No uploads completed"
      return uploadsCompleted.value
  }
}

const mapGetters = () => {
  return Object.fromEntries(
    Object.keys(store.getters).map((getter) => [
      getter,
      computed(() => store.getters[getter]),
    ])
  )
}
const { uploadsInProgress, uploadsCompleted, uploadsFailed } = mapGetters([
  "uploadsInProgress",
  "uploadsCompleted",
  "uploadsFailed",
])

const openFile = (upload) => {
  selectedUpload.value = upload
  if (upload.error) {
    showErrorDialog.value = true
  }
  if (upload.completed && upload.response) {
    router.push({
      name: "File",
      params: { entityName: upload.response.name },
    })
    store.dispatch("clearUploads")
  }
}
</script>
