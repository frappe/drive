<template>
  <div class="bg-surface-white px-1.5 pt-1.5 shadow-2xl rounded-lg w-full">
    <Input
      v-model="searchUserText"
      class="bg-surface-white pb-1.5"
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
        class="flex items-center justify-start px-1.5 py-1 hover:bg-surface-gray-2 w-full rounded cursor-pointer"
        @click="addNewUser(user)"
      >
        <Avatar
          size="sm"
          :label="user.full_name"
          :image="user.user_image"
          class="mr-2"
        />
        <span class="text-base text-ink-gray-7">{{ user.full_name }}</span>
      </li>
    </ul>
    <span
      v-else
      class="rounded-md px-2.5 py-1.5 text-base text-ink-gray-5"
      >No users found</span
    >
    <div class="flex items-center justify-end border-t py-1 mt-1">
      <Button
        class="px-2 py-1.5 hover:bg-surface-gray-2 rounded cursor-pointer"
        @click="resetAll"
      >
        Clear all
      </Button>
    </div>
  </div>
</template>
<script setup>
import { createResource, Avatar, Input } from "frappe-ui"
import { defineEmits, computed, ref, onBeforeUnmount, onMounted } from "vue"
import { set } from "idb-keyval"
import { useRoute } from "vue-router"

const emit = defineEmits(["addNewUsers", "submit"])
const props = defineProps({
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
  submitOnClose: {
    type: Boolean,
    default: false,
    required: false,
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
const allUsers = ref([])
const newUsers = ref([])
const searchUserText = ref("")

const searchFilterUsers = computed(() => {
  if (!searchUserText.value.length) return availableUsers.value
  return availableUsers.value?.filter((x) =>
    x.full_name.toLowerCase().includes(searchUserText.value.toLowerCase())
  )
})

const availableUsers = computed(() => {
  return allUsers.value.filter((item) => !filterActiveUsers(item.user_name))
})

function resetAll() {
  newUsers.value = []
  emit("addNewUsers", newUsers.value)
  fetchData()
}

function filterActiveUsers(val) {
  return (
    props.owner.email === val ||
    props.activeGroups.some((group) => group.user_name === val) ||
    props.activeUsers.some((user) => user.user_name === val)
  )
}

function addNewUser(user) {
  const index = allUsers.value.indexOf(user)
  newUsers.value.push(allUsers.value[index])
  if (index > -1) {
    allUsers.value.splice(index, 1)
  }
  emit("addNewUsers", newUsers.value)
}

onBeforeUnmount(() => {
  if (props.submitOnClose) {
    emit("submit", newUsers.value)
  }
})

onMounted(() => {
  fetchData()
  filterActiveUsers()
})

async function fetchData() {
  userList.fetch({ team: useRoute().params.team })
}

let userList = createResource({
  url: "drive.api.product.get_all_users",
  method: "GET",
  auto: false,
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
    props.searchGroups
      ? set("UsersGroups", JSON.stringify(data))
      : set("Users", JSON.stringify(data))
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
