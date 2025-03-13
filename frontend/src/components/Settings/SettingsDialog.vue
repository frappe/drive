<template>
  <Dialog v-model="open" :options="{ title: 'Settings', size: '5xl' }">
    <template #body>
      <div class="flex" :style="{ height: '80vh' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 py-3 p-4 border-r">
          <h1 class="text-xl font-semibold leading-6 text-gray-900 px-2">
            Settings
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
                class="h-4 w-4 text-gray-700 stroke-[1.5]"
              />
              <span class="text-base text-gray-800">
                {{ tab.label }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-8 pt-6 overflow-y-auto">
          <component
            :is="activeTab.component"
            v-if="activeTab"
            @close="$emit('update:modelValue', false)"
          />
        </div>
        <Button
          class="my-3 mr-4 absolute right-0"
          variant="ghost"
          @click="$emit('update:modelValue', false)"
        >
          <FeatherIcon name="x" class="stroke-2 ml-auto h-4" />
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, defineProps, markRaw, computed } from "vue"
import { Dialog, FeatherIcon, Button } from "frappe-ui"
import ProfileSettings from "@/components/Settings/ProfileSettings.vue"
import StorageSettings from "./StorageSettings.vue"
import User from "@/components/EspressoIcons/User.vue"
import AddUser from "@/components/EspressoIcons/AddUser.vue"
import Cloud from "@/components/EspressoIcons/Cloud.vue"
import UserListSettings from "./UserListSettings.vue"
import { Tag } from "lucide-vue-next"
import TagSettings from "./TagSettings.vue"

let tabs = [
  {
    enabled: true,
    label: "Profile",
    icon: User,
    component: markRaw(ProfileSettings),
  },
  {
    enabled: true,
    label: "Users",
    icon: AddUser,
    component: markRaw(UserListSettings),
  },
  {
    label: "Storage",
    icon: Cloud,
    component: markRaw(StorageSettings),
  },
  {
    label: "Tags",
    icon: Tag,
    component: markRaw(TagSettings),
  },
]

const emit = defineEmits(["update:modelValue"])
const props = defineProps({
  modelValue: String,
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
