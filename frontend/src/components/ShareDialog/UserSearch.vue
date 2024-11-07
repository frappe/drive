<template>
  <div class="grid grid-flow-col grid-cols-12 gap-x-2">
    <div
      class="grid grid-flow-col grid-cols-12 items-center bg-gray-100 rounded text-base h-7 border-gray-400 border"
      :class="showButton ? 'col-span-10' : 'col-span-12'"
    >
      <Popover
        v-slot="{ open }"
        class="min-w-full"
        :class="
          showAccessButton && newUsers.length ? 'col-span-8' : 'col-span-12'
        "
      >
        <Float
          placement="bottom"
          :auto-update="true"
          as="div"
          class="relative"
          :offset="10"
          floating-as="template"
          portal
          adaptive-width
        >
          <PopoverButton
            class="text-left w-full focus:outline-none pl-2 text-gray-600 truncate overflow-hidden"
          >
            <span
              v-for="(user, index) in newUsers"
              :key="user.user_name"
              class="text-gray-800"
            >
              <template v-if="index > 0">, </template>
              {{ user.full_name }}
            </span>
            <span v-if="!newUsers.length" class="w-full">Select users</span>
          </PopoverButton>
          <PopoverPanel
            class="z-10 rounded-lg w-full"
            :class="[
              showButton ? 'max-w-96' : 'max-w-[29rem]',
              showAccessButton && newUsers.length ? 'ml-16' : '',
            ]"
          >
            <UserAutoComplete
              :active-groups="props.activeGroups"
              :active-users="activeUsers.concat(newUsers)"
              :search-groups="props.searchGroups"
              :owner="props.owner"
              :submit-on-close="!showButton"
              @add-new-users="(data) => (newUsers = data)"
              @submit="
                emit('addNewUsers', {
                  users: newUsers,
                  access: newUserAccess,
                }),
                  (newUsers = [])
              "
            />
          </PopoverPanel>
        </Float>
      </Popover>
      <Popover
        v-if="showAccessButton && newUsers.length"
        v-slot="{ open }"
        class="text-gray-700 relative flex-shrink-0 col-span-4 ml-auto border-l border-gray-600"
      >
        <PopoverButton class="flex gap-1 px-2 focus:outline-none">
          {{ newUserAccess.write ? "Can Edit" : "Can View" }}
          <ChevronDown
            :class="{ '[transform:rotateX(180deg)]': open }"
            class="w-4"
          />
        </PopoverButton>
        <PopoverPanel
          class="z-10 bg-white p-1.5 shadow-2xl rounded mt-3 absolute w-full"
          ><ul>
            <li
              class="flex items-center p-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="newUserAccess = { read: 1, write: 0 }"
            >
              <span class="line-clamp-1">Can View</span>
              <Check
                v-if="newUserAccess.read === 1 && newUserAccess.write === 0"
                class="h-3 pl-1"
              />
            </li>
            <li
              class="flex items-center p-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="newUserAccess = { read: 1, write: 1 }"
            >
              Can Edit
              <Check v-if="newUserAccess.write === 1" class="h-3 pl-1" />
            </li></ul
        ></PopoverPanel>
      </Popover>
    </div>
    <Button
      v-if="showButton"
      :disabled="!newUsers.length"
      class="col-span-2"
      :variant="buttonVariant"
      @click="
        emit('addNewUsers', { users: newUsers, access: newUserAccess }),
          (newUsers = [])
      "
    >
      {{ buttonText }}
    </Button>
  </div>
</template>

<script setup>
import { Float } from "@headlessui-float/vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import { defineEmits, ref, watch } from "vue"
import UserAutoComplete from "./UserAutoComplete.vue"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import Check from "@/components/EspressoIcons/Check.vue"

const newUserAccess = ref({ read: 1, write: 0 })
const newUsers = ref([])
const props = defineProps({
  showButton: {
    type: Boolean,
    default: true,
    required: false,
  },
  showAccessButton: {
    type: Boolean,
    default: false,
  },
  buttonText: {
    type: String,
    default: "Share",
  },
  buttonVariant: {
    type: String,
    default: "subtle",
  },
  searchGroups: {
    type: Boolean,
    default: true,
  },
  activeUsers: {
    type: Object,
    required: true,
  },
  activeGroups: {
    type: Object,
    required: true,
  },
  owner: {
    type: Object,
    default() {
      return {
        user_name: "",
      }
    },
  },
})
const emit = defineEmits(["addNewUsers"])
</script>
