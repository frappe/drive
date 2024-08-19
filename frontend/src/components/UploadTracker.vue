<template>
  <div
    class="flex flex-col items-start fixed bottom-0 right-0 w-full m-5 sm:w-96 z-10 rounded-2xl overflow-hidden shadow-2xl 500 bg-white p-4"
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
          <FeatherIcon name="minus" class="h-4 w-4 text-gray-800" />
        </button>
        <button class="focus:outline-none" @click="close">
          <FeatherIcon name="x" class="h-4 w-4 text-gray-800" />
        </button>
      </div>
    </div>
    <div
      class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1 mb-2"
    >
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          currentTab === 1
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="currentTab = 1"
      >
        In Progress
      </Button>
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          currentTab === 2
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="currentTab = 2"
      >
        Completed
      </Button>
      <Button
        v-show="uploadsFailed.length > 0"
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          currentTab === 3
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="currentTab = 3"
      >
        Failed
      </Button>
    </div>
    <div v-if="!collapsed" class="max-h-64 overflow-y-auto bg-white w-full">
      <span
        v-if="!currentTabGetter().length"
        class="px-1.5 text-base font-medium text-gray-800"
        >{{ emptyMessage }}</span
      >
      <div
        v-for="(upload, index) in currentTabGetter()"
        :key="upload.uuid"
        class="cursor-pointer truncate hover:bg-gray-50 rounded px-1 group"
        @mouseover="hoverIndex = index"
        @mouseout="hoverIndex = null"
      >
        <div
          class="flex items-center gap-3 py-2 pr-[3px]"
          @click="openFile(upload)"
        >
          <div class="flex items-center justify-between w-full">
            <div class="flex justify-start items-center w-full max-w-[80%]">
              <File class="w-5 mr-2" />
              <p class="truncate text-sm leading-6 col-span-1 row-span-1">
                {{ upload.name }}
              </p>
            </div>
            <div
              v-if="upload.completed && hoverIndex !== index"
              class="grid h-5 w-5 place-items-center rounded-full text-white bg-black"
              :class="upload.error ? 'bg-red-500' : 'bg-black'"
            >
              <FeatherIcon
                :name="upload.error ? 'x' : 'check'"
                class="h-3 w-3"
                :stroke-width="3"
              />
            </div>
            <FeatherIcon
              v-if="upload.completed && hoverIndex === index"
              class="h-4.5 w-4.5 place-items-center"
              name="external-link"
              :stroke-width="1.5"
            />
            <button
              v-if="hoverIndex === index"
              v-show="!upload.completed && hoverIndex === index"
              class="rounded-full hover:bg-red-300"
              variant="'ghost'"
              @click="emitter.emit('cancelUpload', upload.uuid)"
            >
              <FeatherIcon name="x" class="h-6 w-6 p-1" />
            </button>
            <div
              v-if="hoverIndex !== index"
              v-show="!upload.completed && !upload.error"
              class="h-6 w-6"
            >
              <ProgressRing :radius="14" :progress="upload.progress" />
            </div>
          </div>
        </div>
      </div>
    </div>
    <Dialog
      v-if="showErrorDialog"
      v-model="showErrorDialog"
      :options="{
        title: 'Upload Failed',
        message: selectedUpload.error,
        size: 'sm',
        actions: [
          {
            label: 'Confirm',
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
import { FeatherIcon } from "frappe-ui"
import ProgressRing from "@/components/ProgressRing.vue"
import Dialog from "frappe-ui/src/components/Dialog.vue"
import File from "./EspressoIcons/File.vue"

export default {
  name: "UploadTracker",
  components: {
    FeatherIcon,
    ProgressRing,
    Dialog,
    File,
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
