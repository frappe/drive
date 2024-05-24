<template>
  <Dialog v-model="show" :options="{ title: 'Settings', size: '5xl' }">
    <template #body>
      <div class="flex" :style="{ height: 'calc(100vh - 10rem)' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 py-3 p-4 border-r">
          <h1 class="text-xl font-semibold leading-6 text-gray-900 px-2">
            Settings
          </h1>
          <div class="mt-3 space-y-1">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-gray-200'
                  : 'hover:bg-gray-100',
              ]"
              @click="activeTab = tab"
            >
              <component :is="tab.icon" class="h-4 w-4 text-gray-700" />
              <span class="text-base text-gray-800">
                {{ tab.label }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-12 pt-12 overflow-y-auto">
          <component :is="activeTab.component" v-if="activeTab" />
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
<script>
import { ref, defineProps, markRaw } from "vue"
import { Dialog, FeatherIcon, Button } from "frappe-ui"
import ProfileSettings from "@/components/ProfileSettings.vue"
import UserSettings from "@/components/UserSettings.vue"
import UserRoleSettings from "@/components/UserRoleSettings.vue"
import AboutSettings from "@/components/AboutSettings.vue"
import StorageSettings from "./StorageSettings.vue"
import User from "./EspressoIcons/User.vue"
import Users from "./EspressoIcons/Users.vue"
import Cloud from "./EspressoIcons/Cloud.vue"

let tabs = [
  {
    label: "Profile",
    icon: User,
    component: markRaw(ProfileSettings),
  },
  {
    label: "Users",
    icon: Users,
    component: markRaw(UserSettings),
  },
  {
    label: "Storage",
    icon: Cloud,
    component: markRaw(StorageSettings),
  },
  /*   {
    label: "About",
    icon: Info,
    component: markRaw(AboutSettings),
  },  */
]

let show = defineProps(["modelValue"])
let activeTab = ref(tabs[0])

function closeMenu() {
  let value = false
  this.$emit("update:modelValue", value)
}

export default {
  name: "Settings",
  components: {
    Dialog,
    FeatherIcon,
    Button,
    ProfileSettings,
    UserRoleSettings,
  },
  emits: ["update:modelValue"],
  setup() {
    return { tabs, show, activeTab, closeMenu }
  },
}
</script>
