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
  <div
    class="flex flex-col items-stretch justify-start h-[60%] overflow-y-auto"
  >
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
    class="flex flex-col items-center justify-center h-1/2"
  >
    <FeatherIcon class="h-8 stroke-1 text-gray-600" name="users" />
    <span class="text-gray-800 text-sm mt-2">No Users</span>
  </div>
  <h3 class="my-4 text-base font-medium">Invites</h3>
  <div
    class="text-center text-sm"
    v-if="!invites?.data || !invites.data.length"
  >
    No invites found.
  </div>
  <div v-for="(invite, index) in invites?.data" :key="invite.name">
    <div
      v-if="index > 0"
      class="w-[95%] mx-auto h-px border-t border-gray-200"
    ></div>
    <div class="flex items-center justify-start py-2 pl-2 pr-4 gap-x-3">
      <div class="flex justify-between w-full">
        <span class="text-base">{{ invite.email }}</span>
        <div class="flex">
          <Tooltip
            :text="
              invite.status === 'Proposed'
                ? 'A person from your domain has joined Drive.'
                : 'This invite was sent from your team.'
            "
          >
            <Badge
              :theme="invite.status === 'Pending' ? 'blue' : 'orange'"
              variant="subtle"
              class="my-auto mr-2"
              size="sm"
              >{{ invite.status }}</Badge
            >
          </Tooltip>
          <div class="flex gap-2">
            <Button
              :variant="invite.status === 'Proposed' ? 'ghost' : 'outline'"
              class="my-auto"
              @click="
                rejectInvite.submit({ key: invite.name }),
                  invites.data.splice(index, 1)
              "
            >
              <LucideX v-if="invite.status === 'Proposed'" class="w-4 h-4" />
              <LucideTrash v-else class="w-4 h-4" />
            </Button>

            <Button
              v-if="invite.status === 'Proposed'"
              class="my-auto"
              variant="outline"
              @click="
                acceptInvite.submit({ key: invite.name, redirect: 0 }),
                  invites.data.splice(index, 1)
              "
            >
              <LucideCheck class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
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
          disabled: !emailTest().length && !invited.length,
          loading: () => inviteUsers.loading,
          onClick: () => {
            extractEmails()
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
              @keydown="isValidEmail"
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
import { rejectInvite, acceptInvite } from "@/resources/permissions"
import {
  Avatar,
  FeatherIcon,
  Dropdown,
  Dialog,
  Badge,
  Tooltip,
  createResource,
} from "frappe-ui"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import { XIcon } from "lucide-vue-next"
import { allUsers } from "@/resources/permissions"
import { ref, computed } from "vue"
import { toast } from "@/utils/toasts"
import { useRoute } from "vue-router"
const route = useRoute()
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

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
        team: team.value,
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
        team: team.value,
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
allUsers.fetch({ team: team.value })
function emailTest() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailInput.value
    .split(/,|\s/)
    .filter((email) => email)
    .filter((email) => emailRegex.test(email))
    .filter((email) => !invited.value.includes(email))
}

function extractEmails() {
  invited.value = [...invited.value, ...emailTest()]
  emailInput.value = ""
}

const isAdmin = createResource({
  url: "drive.api.product.is_admin",
  params: { team: team.value },
  auto: true,
})

const inviteUsers = createResource({
  url: "drive.api.product.invite_users",
  onSuccess: () => {
    showInvite.value = false
    toast("Invite sent!")
  },
})

const invites = createResource({
  url: "drive.api.product.get_team_invites",
  auto: true,
  params: { team: team.value },
})

const removeUser = createResource({
  url: "drive.api.product.remove_user",
})

const updateUserRole = createResource({
  url: "drive.api.product.set_role",
})
</script>
