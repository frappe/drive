<template>
  <div
    class="fixed bottom-0 right-0 w-full m-5 sm:w-96 z-10 rounded-md border shadow-[0_4px_12px_#0000001a]"
  >
    <div class="rounded bg-white">
      <div
        class="flex items-center justify-between rounded-t p-4"
        :class="[collapsed ? 'cursor-pointer' : '']"
        @click="collapsed = false"
      >
        <div
          v-if="uploadsInProgress.length > 0"
          class="font-medium truncate text-lg"
        >
          Uploading {{ uploadsInProgress.length }}
          {{ uploadsInProgress.length == 1 ? "item" : "items" }}
        </div>
        <div
          v-else-if="uploadsCompleted.length > 0"
          class="font-medium truncate text-lg"
        >
          {{ uploadsCompleted.length }}
          {{ uploads.length == 1 ? "upload" : "uploads" }} complete
        </div>

        <div class="flex items-center gap-4">
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
        v-if="!collapsed"
        class="max-h-64 overflow-y-auto bg-white rounded-b py-2"
      >
        <div
          v-for="(upload, index) in uploads"
          :key="upload.uuid"
          class="cursor-pointer truncate hover:bg-gray-50 rounded px-2 mx-2"
          @mouseover="hoverIndex = index"
          @mouseout="hoverIndex = null"
        >
          <div class="flex items-center gap-3 py-2 pr-[3px]">
            <div class="flex items-center justify-between w-full">
              <div class="w-full max-w-[80%]">
                <p class="truncate text-sm font-medium leading-6">
                  {{ upload.name }}
                </p>
                <p
                  v-if="upload.error"
                  class="whitespace-pre-wrap text-xs leading-tight text-red-600"
                >
                  {{ upload.error }}
                </p>
              </div>
              <div
                v-if="upload.completed"
                class="grid h-6 w-6 place-items-center rounded-full text-white bg-black"
                :class="upload.error ? 'bg-red-500' : 'bg-black'"
              >
                <FeatherIcon
                  :name="upload.error ? 'x' : 'check'"
                  class="h-4 w-4"
                  :stroke-width="3"
                />
              </div>
              <button
                v-if="hoverIndex === index && upload.progress > 0"
                v-show="!upload.completed && hoverIndex === index"
                class="rounded-full hover:bg-red-300"
                variant="'ghost'"
                @click="emitter.emit('cancelUpload', upload.uuid)"
              >
                <FeatherIcon name="x" class="h-6 w-6 p-1" />
              </button>
              <div
                v-if="hoverIndex !== index && upload.progress > 0"
                v-show="!upload.completed && !upload.error"
                class="h-6 w-6"
              >
                <ProgressRing :radius="14" :progress="upload.progress" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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

export default {
  name: "UploadTracker",
  components: {
    FeatherIcon,
    ProgressRing,
    Dialog,
  },
  data() {
    return {
      collapsed: false,
      hoverIndex: null,
      showCancelDialog: false,
    }
  },
  computed: {
    uploads() {
      return this.$store.state.uploads
    },
    ...mapGetters(["uploadsInProgress", "uploadsCompleted"]),
  },
  methods: {
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
