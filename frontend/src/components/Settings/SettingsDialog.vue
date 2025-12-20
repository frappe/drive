<template>
  <Dialog
    v-model="open"
    :options="{ title: __('Settings'), size: '5xl' }"
  >
    <template #body>
      <div
        class="flex"
        :style="{ height: '80vh' }"
      >
        <div
          class="flex w-52 shrink-0 flex-col bg-surface-menu-bar py-3 p-4 border-r"
        >
          <div class="flex justify-between items-center">
            <h1 class="text-xl font-semibold leading-6 text-ink-gray-9 pr-2">
              {{ __("Settings") }}
            </h1>
            <!-- <Button
              class="ml-auto text-sm"
              variant="ghost"
              label="Exit"
              @click="$emit('update:modelValue', false)"
            /> -->
          </div>
          <div class="mt-3 space-y-1">
            <template
              v-for="tab in tabs"
              :key="tab.label"
            >
              <button
                v-if="tab.enabled?.value !== false"
                class="flex h-7 w-full items-center gap-2 rounded-sm px-2 py-1 focus-visible:outline-none"
                :class="[
                  activeTab?.label == tab.label
                    ? 'bg-surface-gray-4'
                    : 'hover:bg-surface-gray-2',
                ]"
                @click="activeTab = tab"
              >
                <component
                  :is="tab.icon"
                  class="size-4 text-ink-gray-7 stroke-[1.5]"
                />
                <span class="text-base text-ink-gray-8">
                  {{ __(tab.label) }}
                </span>
              </button>
            </template>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-6 py-4">
          <component
            :is="activeTab.component"
            v-if="activeTab"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, markRaw, computed } from "vue"
import { Dialog, Button } from "frappe-ui"
import { isAdmin } from "@/resources/permissions"
import ProfileSettings from "@/components/Settings/ProfileSettings.vue"
import StorageSettings from "./StorageSettings.vue"
import UserListSettings from "./UserListSettings.vue"
import LucideCloudCog from "~icons/lucide/cloud-cog"
import LucideChartBar from "~icons/lucide/chart-bar"
import LucideTag from "~icons/lucide/tag"
import LucideUser from "~icons/lucide/user"
import LucideUserPlus from "~icons/lucide/user-plus"
import TagSettings from "./TagSettings.vue"
import BackendSettings from "./BackendSettings.vue"

const tabs = [
  {
    label: "Profile",
    icon: LucideUser,
    component: markRaw(ProfileSettings),
  },
  {
    label: "Teams",
    icon: LucideUserPlus,
    component: markRaw(UserListSettings),
  },
  {
    label: "Statistics",
    icon: LucideChartBar,
    component: markRaw(StorageSettings),
  },
  {
    label: "Tags",
    icon: LucideTag,
    component: markRaw(TagSettings),
  },
  {
    enabled: computed(() => isAdmin.data?.is_admin || false),
    label: "Storage",
    icon: LucideCloudCog,
    component: markRaw(BackendSettings),
  },
]
if (!isAdmin.data) isAdmin.fetch()

const emit = defineEmits(["update:modelValue"])
const props = defineProps({
  modelValue: Boolean,
  suggestedTab: Number,
})
const activeTab = ref(tabs[props.suggestedTab])

const open = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})
</script>
