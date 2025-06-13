<template>
  <Dialog v-model="open" :options="{ title: 'Settings', size: '5xl' }">
    <template #body>
      <div class="flex" :style="{ height: '80vh' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 py-3 p-4 border-r">
          <h1 class="text-xl font-semibold leading-6 text-gray-900 px-2">
            {{ __("Settings") }}
          </h1>
          <div class="mt-3 space-y-1">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              class="flex h-7 w-full items-center gap-2 rounded-sm px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-gray-300'
                  : 'hover:bg-gray-100',
              ]"
              @click="activeTab = tab"
            >
              <component
                :is="tab.icon"
                class="size-4 text-gray-700 stroke-[1.5]"
              />
              <span class="text-base text-gray-800">
                {{ __(tab.label) }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-8 pt-6 overflow-y-auto">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
        <Button
          class="my-2 mr-2 absolute right-0"
          variant="ghost"
          @click="$emit('update:modelValue', false)"
        >
          <LucideX class="ml-auto size-4" />
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, defineProps, markRaw, computed } from "vue"
import { Dialog, Button } from "frappe-ui"
import ProfileSettings from "@/components/Settings/ProfileSettings.vue"
import StorageSettings from "./StorageSettings.vue"
import UserListSettings from "./UserListSettings.vue"
import {
  LucideCloudCog,
  LucideTag,
  LucideUser,
  LucideUserPlus,
} from "lucide-vue-next"
import TagSettings from "./TagSettings.vue"

let tabs = [
  {
    enabled: true,
    label: "Profile",
    icon: LucideUser,
    component: markRaw(ProfileSettings),
  },
  {
    enabled: true,
    label: "Users",
    icon: LucideUserPlus,
    component: markRaw(UserListSettings),
  },
  {
    label: "Storage",
    icon: LucideCloudCog,
    component: markRaw(StorageSettings),
  },
  {
    label: "Tags",
    icon: LucideTag,
    component: markRaw(TagSettings),
  },
]

const emit = defineEmits(["update:modelValue"])
const props = defineProps({
  modelValue: Boolean,
  suggestedTab: Number,
})
let activeTab = ref(tabs[props.suggestedTab])

const open = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})
</script>
