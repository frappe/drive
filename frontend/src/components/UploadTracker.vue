<template>
  <Teleport to="#modals">
    <div class="fixed bottom-0 right-0 w-full p-6 sm:w-96 z-10">
      <div class="rounded-lg bg-white shadow-lg">
        <div
          class="flex items-center justify-between rounded-sm bg-gray-50 p-4"
          :class="{ shadow: !collapsed }">
          <div v-if="uploadsInProgress.length > 0" class="text-sm">
            Uploading {{ uploadsInProgress.length }}
            {{ uploadsInProgress.length == 1 ? "item" : "items" }}
          </div>
          <div v-else-if="uploadsCompleted.length > 0" class="text-sm">
            {{ uploadsCompleted.length }}
            {{ uploads.length == 1 ? "upload" : "uploads" }} complete
          </div>

          <div class="flex items-center gap-4">
            <button class="focus:outline-none" @click="toggleCollapsed">
              <FeatherIcon
                :name="collapsed ? 'chevron-up' : 'chevron-down'"
                class="h-5 w-5 text-gray-800" />
            </button>
            <button
              v-if="uploads.length === uploadsCompleted.length"
              class="focus:outline-none"
              @click="close">
              <FeatherIcon name="x" class="h-5 w-5 text-gray-800" />
            </button>
          </div>
        </div>
        <div v-if="!collapsed" class="max-h-64 overflow-y-auto bg-white">
          <div
            v-for="upload in uploads"
            :key="upload.uuid"
            class="truncate border-b">
            <div class="flex items-center gap-3 p-4">
              <div
                v-if="upload.completed"
                class="m-[0.125rem] flex h-7 w-7 items-center justify-center rounded-full p-1 text-white"
                :class="upload.error ? 'bg-red-400' : 'bg-[#59B179]'">
                <FeatherIcon
                  :name="upload.error ? 'x' : 'check'"
                  class="h-3.5 w-3.5"
                  :stroke-width="2.5" />
              </div>
              <div v-else class="h-8 w-8 rounded-full">
                <ProgressRing
                  v-show="true"
                  :radius="16"
                  :progress="upload.progress" />
              </div>
              <div class="flex-1 truncate">
                <p class="truncate text-sm font-medium leading-6">
                  {{ upload.name }}
                </p>
                <p
                  v-if="upload.error"
                  class="whitespace-pre-wrap text-xs leading-tight text-red-600">
                  {{ upload.error }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script>
import { mapGetters } from "vuex";
import { FeatherIcon } from "frappe-ui";
import ProgressRing from "@/components/ProgressRing.vue";

export default {
  name: "UploadTracker",
  components: {
    FeatherIcon,
    ProgressRing,
  },
  data() {
    return {
      collapsed: false,
    };
  },
  computed: {
    uploads() {
      return this.$store.state.uploads;
    },
    ...mapGetters(["uploadsInProgress", "uploadsCompleted"]),
  },
  methods: {
    toggleCollapsed() {
      this.collapsed = !this.collapsed;
    },
    close() {
      this.$store.dispatch("clearUploads");
    },
  },
};
</script>
