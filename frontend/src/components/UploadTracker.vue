<template>
  <portal to="modals">
    <div
      class="fixed bottom-0 right-0 flex items-start justify-end px-4 py-6 pointer-events-none sm:p-6"
    >
      <div
        class="max-w-xs w-64 bg-white rounded-lg shadow-lg pointer-events-auto"
      >
        <div
          class="flex flex-shrink-0 items-center justify-between p-4 rounded-sm bg-gray-50"
        >
          <div class="text-sm">
            Uploading {{ uploadsInProgress.length }}
            {{ uploadsInProgress.length == 1 ? 'item' : 'items' }}
          </div>
        </div>
        <div class="max-h-64 overflow-y-auto">
          <div
            class="truncate border-b"
            v-for="upload in uploadsInProgress"
            :key="upload.uuid"
          >
            <div class="p-4 flex gap-3 items-center">
              <div class="w-8 h-8 rounded-full">
                <ProgressRing
                  v-show="true"
                  radius="16"
                  :progress="upload.progress"
                />
              </div>
              <div class="flex-1 truncate">
                <p class="text-sm font-medium leading-6 text-gray-900 truncate">
                  {{ upload.name }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </portal>
</template>
<script>
import ProgressRing from '@/components/ProgressRing.vue'

export default {
  name: 'UploadTracker',
  components: {
    ProgressRing,
  },
  computed: {
    uploadsInProgress() {
      return this.$store.state.uploads.inProgress
    },
  },
}
</script>
