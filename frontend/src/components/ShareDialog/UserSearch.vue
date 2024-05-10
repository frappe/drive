<template>
  <div class="grid grid-flow-col grid-cols-12 gap-x-2">
    <div
      class="flex items-center justify-start col-span-10 bg-gray-100 rounded text-base"
    >
      <Popover v-slot="{ open }" class="relative w-full">
        <PopoverButton
          class="text-left w-full max-w-56 focus:outline-none pl-2 text-gray-600 truncate overflow-hidden"
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
          class="z-10 bg-white px-1.5 pt-1.5 shadow-2xl rounded-lg mt-3 absolute w-full"
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
            class="flex flex-col items-start justify-start max-h-[8rem] overflow-y-auto"
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
              {{ user.full_name }}
            </li>
          </ul>
          <span v-else class="rounded-md px-2.5 py-1.5 text-base text-gray-600"
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
      </Popover>

      <div class="border-l border-gray-300 h-5"></div>

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
      </Popover>
    </div>
    <Button
      class="col-span-2"
      variant="solid"
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
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import { defineEmits, computed, ref } from "vue"
import { createResource, Avatar, Input, FeatherIcon } from "frappe-ui"

const searchUserText = ref("")
const allUsers = ref([])
const newUserAccess = ref({ read: 1, write: 0 })
const newUsers = ref([])
const props = defineProps(["owner", "activeUsers", "activeGroups"])
const emit = defineEmits(["addNewUsers"])

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
  url: "drive.utils.users.get_users_with_drive_user_role_and_groups",
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
