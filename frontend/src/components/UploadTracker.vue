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
              v-if="upload.completed"
            >
              <LucideInfo
                v-if="upload.error"
                class="size-4 text-ink-gray-6"
              />
              <LucideFolderOpenDot
                v-else
                class="size-4 text-ink-gray-6 place-items-center"
              />
            </Button>
            <Button
              v-if="hoverIndex === index"
              v-show="!upload.completed && hoverIndex === index"
              variant="ghost"
              class="rounded-full hover:bg-surface-red-4"
              @click="emitter.emit('cancelUpload', upload.uuid)"
            >
              <LucideX class="h-6 w-6 p-1" />
            </Button>
            <div
              v-if="hoverIndex !== index"
              v-show="!upload.completed && !upload.error"
              class="h-6 w-6"
            >
              <ProgressRing
                :radius="14"
                :progress="upload.progress"
              />
            </div>
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
    <Dialog
      v-if="showCancelDialog"
      v-model="showCancelDialog"
      :options="{
        title: 'Cancel uploads',
        message: 'Are you sure you want to cancel all ongoing uploads?',
        size: 'sm',
        actions: [
          {
            label: 'Confirm',
            variant: 'subtle',
            theme: 'red',
            onClick: () => {
              emitter.emit('cancelAllUploads')
              showCancelDialog = false
              $store.dispatch('clearUploads')
            },
          },
        ],
      }"
    />
  </div>
</template>
<script>
import { mapGetters } from "vuex"
import { Dialog, TabButtons } from "frappe-ui"
import ProgressRing from "@/components/ProgressRing.vue"

export default {
  name: "UploadTracker",
  components: {
    ProgressRing,
    Dialog,
    TabButtons,
  },
  data() {
    return {
      collapsed: false,
      hoverIndex: null,
      showCancelDialog: false,
      showErrorDialog: false,
      selectedUpload: null,
      currentTab: 1,
      emptyMessage: "No uploads in progress",
    }
  },
  computed: {
    uploads() {
      return this.$store.state.uploads
    },
    ...mapGetters(["uploadsInProgress", "uploadsCompleted", "uploadsFailed"]),
  },
  methods: {
    currentTabGetter() {
      switch (this.currentTab) {
        case 1:
          this.emptyMessage = "No uploads in progress"
          return this.uploadsInProgress
        case 2:
          this.emptyMessage = "No uploads completed"
          return this.uploadsCompleted
        case 3:
          this.emptyMessage = "No failed uploads"
          return this.uploadsFailed
        default:
          this.emptyMessage = "No uploads completed"
          return this.uploadsCompleted
      }
    },
    openFile(upload) {
      this.selectedUpload = upload
      if (upload.error) {
        console.log(upload.response)
        this.showErrorDialog = true
      }
      if (upload.completed && upload.response) {
        this.$router.push({
          name: "File",
          params: { entityName: upload.response.name },
        })
        this.close()
      }
    },
    toggleCollapsed() {
      this.collapsed = !this.collapsed
    },
    close() {
      if (this.uploads.length === this.uploadsCompleted.length) {
        this.$store.dispatch("clearUploads")
      } else {
        this.showCancelDialog = true
      }
    },
  },
}
</script>
