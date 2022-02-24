<template>
  <portal to="modals">
    <div
      class="fixed bottom-0 right-0 flex items-start justify-end px-4 py-6 pointer-events-none sm:p-6"
    >
      <div
        class="max-w-xs w-full sm:w-64 bg-white rounded-lg shadow-lg pointer-events-auto"
      >
        <div
          class="flex flex-shrink-0 items-center justify-between p-4 rounded-sm bg-gray-50"
          :class="{ shadow: !collapsed }"
        >
          <div v-if="uploadsInProgress.length > 0" class="text-sm">
            Uploading {{ uploadsInProgress.length }}
            {{ uploadsInProgress.length == 1 ? 'item' : 'items' }}
          </div>
          <div v-else-if="uploadsCompleted.length > 0" class="text-sm">
            {{ uploadsCompleted.length }}
            {{ uploads.length == 1 ? 'upload' : 'uploads' }} complete
          </div>
          <div class="flex items-center gap-4">
            <button @click="toggleCollapsed" class="focus:outline-none">
              <FeatherIcon
                :name="collapsed ? 'chevron-up' : 'chevron-down'"
                class="w-5 h-5 text-gray-800"
              />
            </button>
            <button
              v-if="uploads.length === uploadsCompleted.length"
              @click="closeUploadTracker"
              class="focus:outline-none"
            >
              <FeatherIcon name="x" class="w-5 h-5 text-gray-800" />
            </button>
          </div>
        </div>
        <div class="max-h-64 overflow-y-auto" v-if="!collapsed">
          <div
            class="truncate border-b"
            v-for="upload in uploads"
            :key="upload.uuid"
          >
            <div class="p-4 flex gap-3 items-center">
              <div
                v-if="upload.completed"
                class="w-7 h-7 p-1 rounded-full bg-[#59B179]"
              >
                <GreenCheckIcon />
              </div>
              <div v-else class="w-8 h-8 rounded-full">
                <ProgressRing
                  v-show="true"
                  :radius="16"
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
import { mapGetters } from 'vuex'
import { FeatherIcon, GreenCheckIcon } from 'frappe-ui'
import ProgressRing from '@/components/ProgressRing.vue'

export default {
  name: 'UploadTracker',
  components: {
    FeatherIcon,
    ProgressRing,
    GreenCheckIcon,
  },
  data() {
    return {
      collapsed: false,
    }
  },
  computed: {
    uploads() {
      return this.$store.state.uploads
    },
    ...mapGetters(['uploadsInProgress', 'uploadsCompleted']),
  },
  methods: {
    toggleCollapsed() {
      this.collapsed = !this.collapsed
    },
    closeUploadTracker() {
      this.$store.dispatch('clearUploads')
    },
  },
}
</script>
