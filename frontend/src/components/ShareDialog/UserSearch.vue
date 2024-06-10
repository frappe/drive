<template>
  <div class="grid grid-flow-col grid-cols-12 gap-x-2">
    <div
      class="flex items-center justify-start col-span-10 bg-gray-100 rounded text-base"
    >
      <Popover v-slot="{ open }" class="min-w-full">
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
            class="text-left w-full max-w-full focus:outline-none pl-2 text-gray-600 truncate overflow-hidden"
          >
            <span
              v-for="(user, index) in newUsers"
              :key="user.user_name"
              class="text-gray-800"
            >
              <template v-if="index > 0">, </template>
              {{ user.full_name }}
            </span>
            <span v-if="!newUsers.length" class="">Add users</span>
          </PopoverButton>
          <PopoverPanel
            class="z-10 bg-white px-1.5 pt-1.5 shadow-2xl rounded-lg max-w-96 w-full"
          >
            <Input
              v-model="searchUserText"
              class="bg-white pb-1.5"
              placeholder="Search users"
              type="text"
              @input="searchUserText = $event"
            />
            <ul
              v-if="searchFilterUsers?.length"
              class="flex flex-col items-start justify-start max-h-[10rem] overflow-y-auto"
            >
              <li
                v-for="user in searchFilterUsers"
                :key="user.email"
                class="flex items-center justify-start px-1.5 py-1 hover:bg-gray-100 w-full rounded cursor-pointer"
                @click="addNewUser(user)"
              >
                <Avatar
                  size="sm"
                  :label="user.full_name"
                  :image="user.user_image"
                  class="mr-2"
                />
                <span class="text-base text-gray-700">{{
                  user.full_name
                }}</span>
              </li>
            </ul>
            <span
              v-else
              class="rounded-md px-2.5 py-1.5 text-base text-gray-600"
              >No users found</span
            >
            <div class="flex items-center justify-end border-t py-1 mt-1">
              <Button
                class="px-2 py-1.5 hover:bg-gray-100 rounded cursor-pointer"
                @click="resetAll"
              >
                Clear all
              </Button>
            </div>
          </PopoverPanel>
        </Float>
      </Popover>

      <!--       <div class="border-l border-gray-300 h-5"></div>

      <Popover v-slot="{ open }" class="text-gray-700 relative flex-shrink-0">
        <PopoverButton class="flex gap-1 px-2 focus:outline-none">
          {{ newUserAccess.write ? "Can Edit" : "Can View" }}
          <FeatherIcon name="chevron-down" class="w-4" />
        </PopoverButton>
        <PopoverPanel
          class="z-10 bg-white p-1.5 shadow-2xl rounded mt-3 absolute w-full"
          ><ul>
            <li
              class="line-clamp-1 p-1 pl-1.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="newUserAccess = { read: 1, write: 0 }"
            >
              Can View
            </li>
            <li
              class="line-clamp-1 p-1 pl-1.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="newUserAccess = { read: 1, write: 1 }"
            >
              Can Edit
            </li>
          </ul></PopoverPanel
        >
      </Popover> -->
    </div>
    <Button
      class="col-span-2"
      :variant="buttonVariant"
      @click="
        emit('addNewUsers', { users: newUsers, access: newUserAccess }),
          (newUsers = [])
      "
    >
      Invite
    </Button>
  </div>
</template>

<script setup>
import { Float } from "@headlessui-float/vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import { defineEmits, computed, ref, watch } from "vue"
import { createResource, Avatar, Input } from "frappe-ui"

const searchUserText = ref("")
const allUsers = ref([])
const newUserAccess = ref({ read: 1, write: 0 })
const newUsers = ref([])
const props = defineProps({
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
const activeUsers = ref(props.activeUsers)
const activeGroups = ref(props.activeGroups)
const emit = defineEmits(["addNewUsers"])

watch([activeUsers.value, activeGroups.value], () => {
  allUsers.value = [...fetchAllUsers.data]
})

const searchFilterUsers = computed(() => {
  if (!searchUserText.value.length) return availableUsers.value
  return availableUsers.value?.filter((x) =>
    x.full_name.toLowerCase().includes(searchUserText.value.toLowerCase())
  )
})

const availableUsers = computed(() => {
  return allUsers.value.filter((item) => !filterActiveUsers(item.user_name))
})

function addNewUser(user) {
  const index = allUsers.value.indexOf(user)
  newUsers.value.push(allUsers.value[index])
  if (index > -1) {
    allUsers.value.splice(index, 1)
  }
}

function filterActiveUsers(val) {
  return (
    props.owner.email === val ||
    props.activeGroups.some((group) => group.user_name === val) ||
    props.activeUsers.some((user) => user.user_name === val)
  )
}

function resetAll() {
  newUsers.value = []
  allUsers.value = fetchAllUsers.fetch().then(() => {})
}

let fetchAllUsers = createResource({
  url: props.searchGroups
    ? "drive.utils.users.get_users_with_drive_user_role_and_groups"
    : "drive.utils.users.get_users_with_drive_user_role",
  method: "GET",
  auto: true,
  onSuccess(data) {
    // Update group key to filter
    data.forEach(function (item) {
      if (item.email) {
        item.user_name = item.email
        item.user_type = "User"
        delete item.email
      } else {
        item.full_name = item.name
        item.user_name = item.name
        item.user_type = "User Group"
        delete item.name
      }
    })
    allUsers.value = [...data]
  },
  onError(error) {
    if (error.messages) {
      this.errorMessage = error.messages.join("\n")
    } else {
      this.errorMessage = error.message
    }
  },
})
</script>
