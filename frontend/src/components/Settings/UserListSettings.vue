<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold">Users</h1>
    <Button
      v-if="$resources.isAdmin?.data"
      variant="solid"
      icon-left="plus"
      class="ml-auto mr-4"
      @click="showInviteUserDialog = true"
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
          v-if="
            $resources.isAdmin.data && user.name != $store.state.user.fullName
          "
          :options="getRoleOptions(user)"
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
    v-model="showInviteUserDialog"
    :options="{
      title: 'Invite User',
      size: 'lg',
      actions: [
        {
          label: 'Send Invitation',
          variant: 'solid',
          disabled: !emailsToInvite.length,
          loading: $resources.inviteUsers.loading,
          onClick: () => {
            $resources.inviteUsers.submit({
              emails: emailsToInvite.join(','),
              role: NewUserRole,
            })
            showInviteUserDialog = false
          },
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex items-start justify-start gap-4">
        <div class="flex flex-wrap gap-1 rounded w-full bg-gray-100 p-0.5">
          <Button
            v-for="(email, idx) in emailsToInvite"
            :key="email"
            :label="email"
            variant="outline"
            class="shadow-sm"
          >
            <template #suffix>
              <XIcon
                class="h-4"
                stroke-width="1.5"
                @click.stop="() => emailsToInvite.splice(idx, 1)"
              />
            </template>
          </Button>
          <div class="min-w-[10rem] flex-1">
            <input
              v-model="emailsTxt"
              type="text"
              autocomplete="off"
              placeholder="Enter email address"
              class="h-7 w-full rounded border-none bg-gray-100 py-1.5 pl-2 pr-2 text-base text-gray-800 placeholder-gray-500 transition-colors focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
              @keydown.enter.capture.stop="extractEmails(`${emailsTxt} `)"
            />
          </div>
        </div>
        <div>
          <Popover
            v-slot="{ open, close }"
            class="text-gray-700 relative flex-shrink-0 col-span-3 justify-self-end row-start-1 row-end-1"
          >
            <PopoverButton
              class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-8 items-center text-base justify-self-end min-w-20"
            >
              {{ NewUserRole.slice(NewUserRole.indexOf(" ") + 1) }}
              <FeatherIcon
                :class="{ '[transform:rotateX(180deg)]': open }"
                name="chevron-down"
                class="w-4 ml-auto"
              />
            </PopoverButton>
            <PopoverPanel
              class="z-10 bg-white p-1 shadow-2xl rounded mt-1 absolute"
              ><ul>
                <li
                  class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                  @click=";(NewUserRole = 'Drive Guest'), close()"
                >
                  Guest
                  <Check v-if="NewUserRole === 'Drive Guest'" class="h-3" />
                </li>
                <li
                  class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                  @click=";(NewUserRole = 'Drive User'), close()"
                >
                  User
                  <Check v-if="NewUserRole === 'Drive User'" class="h-3" />
                </li></ul
            ></PopoverPanel>
          </Popover>
        </div>
      </div>
    </template>
  </Dialog>
  <Dialog
    v-if="showRemoveUserDialog"
    v-model="showRemoveUserDialog"
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
          loading: $resources.removeUser.loading,
          onClick: () => {
            $resources.removeUser.submit({
              user_id: selectedUser.name,
              team,
            })
            allUsers.data.splice(allUsers.data.indexOf(selectedUser), 1)
            showRemoveUserDialog = false
          },
        },
      ],
    }"
  >
  </Dialog>
</template>

<script>
import { h } from "vue"
import { Avatar, FeatherIcon, Dropdown, Dialog } from "frappe-ui"
import RoleDetailsDialog from "@/components/RoleDetailsDialog.vue"
import NewRoleDialog from "./NewRoleDialog.vue"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import { XIcon } from "lucide-vue-next"
import Check from "@/components/EspressoIcons/Check.vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import { allUsers } from "@/resources/permissions"
import { toast } from "@/utils/toasts.js"

const team = localStorage.getItem("recentTeam")
export default {
  name: "UserRoleSettings",
  components: {
    Avatar,
    RoleDetailsDialog,
    NewRoleDialog,
    FeatherIcon,
    Dropdown,
    Dialog,
    XIcon,
    Popover,
    PopoverButton,
    PopoverPanel,
    Check,
    ChevronDown,
  },
  data() {
    return {
      allUsers,
      team,
      RoleName: "",
      UsersInRole: [],
      NewUserRole: "Drive User",
      CreateRoleDialog: false,
      EditRoleDialog: false,
      AllRoles: null,
      errorMessage: "",
      activeGroup: null,
      showDeleteDialog: false,
      showInviteUserDialog: false,
      showRemoveUserDialog: false,
      emailsToInvite: "",
      emailsTxt: "",
      selectedUser: null,
    }
  },
  computed: {
    memberEmails() {
      let x = []
      this.UsersInRole.forEach((user) => x.push(user.email))
      return x
    },
  },
  methods: {
    getRoleOptions() {
      return [
        {
          label: "Manager",
          onClick: () => {
            this.selectedUser.role = "admin"
            this.$resources.updateUserRole.submit({
              team,
              user_id: this.selectedUser.name,
              role: 1,
            })
          },
        },
        {
          label: "User",
          onClick: () => {
            this.selectedUser.role = "user"
            this.$resources.updateUserRole.submit({
              team,
              user_id: this.selectedUser.name,
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
                onClick: () => (this.showRemoveUserDialog = true),
              },
              "Remove"
            ),
        },
      ]
    },
    extractEmails(emails) {
      const lastChar = emails.slice(-1)
      if (![" ", ","].includes(lastChar)) {
        this.emailsTxt = emails
        return
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      const newEmails = emails
        .split(/,|\s/)
        .filter((email) => email)
        .filter((email) => emailRegex.test(email))
        .filter((email) => !this.emailsToInvite.includes(email))
      this.emailsToInvite = [...this.emailsToInvite, ...newEmails]
      this.emailsTxt = ""
    },
  },
  resources: {
    isAdmin: {
      url: "drive.utils.users.is_admin",
      params: { team },
      auto: true,
    },
    inviteUsers: {
      url: "drive.utils.users.invite_users",
      method: "POST",
      auto: false,
      onError(error) {
        if (error.messages) {
          this.errorMessage = error.messages.join("\n")
        } else {
          this.errorMessage = error.message
        }
      },
    },
    removeUser: {
      url: "drive.utils.users.remove_user",
    },
    updateUserRole: {
      url: "drive.utils.users.set_role",
    },
  },
}
</script>
