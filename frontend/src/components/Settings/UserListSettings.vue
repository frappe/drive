<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold">Users</h1>
    <Button
      v-if="isAdmin?.data"
      variant="solid"
      icon-left="plus"
      class="ml-auto mr-4"
      @click="
        () => {
          showInvite = true
        }
      "
    >
      Invite
    </Button>
  </div>
  <div class="flex flex-col items-stretch justify-start overflow-y-auto">
    <div class="flex items-center justify-between"></div>
    <div v-for="(user, index) in allUsers?.data" :key="user.user_name">
      <div
        v-if="index > 0"
        class="w-[95%] mx-auto h-px border-t border-gray-200"
      ></div>
      <div class="flex items-center justify-start py-2 pl-2 pr-4 gap-x-3">
        <Avatar :image="user.user_image" :label="user.full_name" size="lg" />
        <div class="flex flex-col">
          <span class="text-base">{{ user.full_name }}</span>
          <span class="text-xs text-gray-700">{{ user.user_name }}</span>
        </div>
        <Dropdown
          v-if="isAdmin.data && user.name != $store.state.user.fullName"
          :options="roleOptions"
          v-slot="{ open }"
          placement="right"
          class="ml-auto text-base text-gray-600"
        >
          <Button variant="ghost" @click="selectedUser = user"
            >{{ user.role == "admin" ? "Manager" : "User" }}
            <template #suffix>
              <ChevronDown :class="{ '[transform:rotateX(180deg)]': open }" />
            </template>
          </Button>
        </Dropdown>
        <span v-else class="ml-auto text-base text-gray-600">{{
          user.role == "admin" ? "Manager" : "User"
        }}</span>
      </div>
    </div>
  </div>
  <div
    v-if="!allUsers?.data?.length"
    class="h-1/2 w-full flex flex-col items-center justify-center my-auto"
  >
    <FeatherIcon class="h-8 stroke-1 text-gray-600" name="users" />
    <span class="text-gray-800 text-sm mt-2">No Users</span>
  </div>
  <Dialog
    v-model="showInvite"
    :options="{
      title: 'Invite people to ' + getTeams.data[team].title,
      size: 'lg',
      actions: [
        {
          label: 'Send Invitation',
          variant: 'solid',
          disabled: !invited.length,
          loading: inviteUsers.loading,
          onClick: () => {
            inviteUsers.submit({
              emails: invited.join(','),
              team,
            })
            dialog = null
          },
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex items-start justify-start gap-4">
        <div class="flex flex-wrap gap-1 rounded w-full bg-gray-100 p-2">
          <Button
            v-for="(email, idx) in invited"
            :key="email"
            :label="email"
            variant="outline"
            class="shadow-sm"
          >
            <template #suffix>
              <XIcon
                class="h-4"
                stroke-width="1.5"
                @click.stop="() => invited.splice(idx, 1)"
              />
            </template>
          </Button>
          <div class="min-w-[10rem] flex-1">
            <input
              v-model="emailInput"
              type="text"
              autocomplete="off"
              placeholder="Enter email address"
              class="h-7 w-full rounded border-none bg-gray-100 py-1.5 pl-2 pr-2 text-base text-gray-800 placeholder-gray-500 transition-colors focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
              @keydown.enter.capture.stop="extractEmails"
              @keydown.space.prevent.stop="extractEmails"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
  <Dialog
    v-if="showRemove"
    v-model="showRemove"
    :options="{
      title: 'Are you sure?',
      size: 'md',
      message: `Removing ${selectedUser.full_name} will completely revoke their access to your team. You can always add them back using the same email ID.`,
      actions: [
        {
          variant: 'solid',
          theme: 'red',
          label:
            'I confirm that I want to remove ' + selectedUser.full_name + '.',
          loading: removeUser.loading,
          onClick: () => {
            removeUser.submit({
              user_id: selectedUser.name,
              team,
            })
            allUsers.data.splice(allUsers.data.indexOf(selectedUser), 1)
            showRemove = false
          },
        },
      ],
    }"
  >
  </Dialog>
</template>

<script setup>
import { h } from "vue"
import { getTeams } from "@/resources/files"
import {
  Avatar,
  FeatherIcon,
  Dropdown,
  Dialog,
  createResource,
} from "frappe-ui"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import { XIcon } from "lucide-vue-next"
import { allUsers } from "@/resources/permissions"
import { ref, computed } from "vue"

const team = localStorage.getItem("recentTeam")

const dialog = ref(null)
const selectedUser = ref(null)
const invited = ref("")
const emailInput = ref("")
const showInvite = ref(false)
const showRemove = ref(false)

const roleOptions = [
  {
    label: "Manager",
    onClick: () => {
      selectedUser.value.role = "admin"
      updateUserRole.submit({
        team,
        user_id: selectedUser.value.name,
        role: 1,
      })
    },
  },
  {
    label: "User",
    onClick: () => {
      selectedUser.value.role = "user"
      updateUserRole.submit({
        team,
        user_id: selectedUser.value.name,
        role: 0,
      })
    },
  },
  {
    label: "Remove",
    class: "text-red-500",
    component: () =>
      h(
        "button",
        {
          class: [
            "group flex w-full items-center text-red-500 rounded-md px-2 py-2 text-sm",
          ],
          onClick: () => (showRemove.value = true),
        },
        "Remove"
      ),
  },
]

function extractEmails() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const newEmails = emailInput.value
    .split(/,|\s/)
    .filter((email) => email)
    .filter((email) => emailRegex.test(email))
    .filter((email) => !invited.value.includes(email))
  invited.value = [...invited.value, ...newEmails]
  emailInput.value = ""
}

const isAdmin = createResource({
  url: "drive.utils.users.is_admin",
  params: { team },
  auto: true,
})

const inviteUsers = createResource({
  url: "drive.utils.users.invite_users",
  // onError(error) {
  //   if (error.messages) {
  //     this.errorMessage = error.messages.join("\n")
  //   } else {
  //     this.errorMessage = error.message
  //   }
  // },
})
const removeUser = createResource({
  url: "drive.utils.users.remove_user",
})

const updateUserRole = createResource({
  url: "drive.utils.users.set_role",
})
</script>
