<template>
  <Dialog v-model="show" :options="{ title: 'Settings', size: '5xl' }">
    <template #body>
      <div class="flex" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 py-3 p-4 border-r">
          <h1 class="text-xl font-semibold leading-6 text-gray-900 px-2">
            Settings
          </h1>
          <div class="mt-3 space-y-1">
            <button
              class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-gray-200'
                  : 'hover:bg-gray-100',
              ]"
              v-for="tab in tabs"
              :key="tab.label"
              @click="activeTab = tab">
              <component :is="tab.icon" class="h-4 w-4 text-gray-700" />
              <span class="text-base text-gray-800">
                {{ tab.label }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-16 pt-12">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
        <Button
          class="my-3 mr-4"
          variant="minimal"
          @click="$emit('update:modelValue', false)">
          <FeatherIcon name="x" class="stroke-2 ml-auto h-4" />
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { ref, defineProps, defineEmits, markRaw } from "vue";
import { Dialog, FeatherIcon, Button } from "frappe-ui";
import { UserCog, Users } from "lucide-vue-next";
import ProfileSettings from "@/components/ProfileSettings.vue";
import UserRoleSettings from "./UserRoleSettings.vue";

let tabs = [
  /*   {
    label: "My Profile",
    icon: UserCog,
    component: markRaw(ProfileSettings),
  }, */
  {
    label: "User Groups",
    icon: Users,
    component: markRaw(UserRoleSettings),
  },
];

const emit = defineEmits(["update:modelValue"]);

let show = defineProps(["modelValue"]);
let activeTab = ref(tabs[0]);

function closeMenu() {
  let value = false;
  emit("update:modelValue", value);
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
  setup() {
    return { tabs, show, activeTab, closeMenu };
  },
};
</script>
