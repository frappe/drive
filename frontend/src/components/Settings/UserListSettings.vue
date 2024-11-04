<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold">Users</h1>
    <Button
      v-if="$store.state.user.role === 'Drive Admin'"
      variant="solid"
      icon-left="plus"
      class="ml-auto"
      @click="showInviteUserDialog = true"
    >
      Invite
    </Button>
  </div>
  <div class="flex flex-col items-stretch justify-start overflow-y-auto">
    <div class="flex items-center justify-between"></div>
    <div
      v-for="(user, index) in $resources.fetchAllUsers?.data"
      :key="user.user_name"
    >
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
          v-if="$store.state.user.role === 'Drive Admin'"
          v-slot="{ open }"
          :options="getRoleOptions(user)"
          placement="right"
          class="ml-auto text-base text-gray-600"
        >
          <Button variant="ghost" @click="selectedUser = user"
            >{{ user.role }}
            <template #suffix>
              <ChevronDown />
            </template>
          </Button>
        </Dropdown>
        <span v-else class="ml-auto text-base text-gray-600">{{
          user.role
        }}</span>
      </div>
    </div>
  </div>
  <div
    v-if="!$resources.fetchAllUsers?.data?.length"
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
      title: 'Remove User',
      size: 'md',
      message: `Removing ${selectedUser.full_name} will revoke their access to Frappe Drive. All files and folders owned by them will remain intact. You can add them back using the same email address.
`,
      actions: [
        {
          variant: 'solid',
          theme: 'red',
          label: 'Remove',
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
  </Dialog>
</template>

<script>
import { h } from "vue"
import { Avatar, FeatherIcon, Dropdown, Dialog } from "frappe-ui"
import RoleDetailsDialog from "@/components/RoleDetailsDialog.vue"
import NewRoleDialog from "./NewRoleDialog.vue"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import { PlusIcon, SearchIcon, XIcon } from "lucide-vue-next"
import Check from "@/components/EspressoIcons/Check.vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import disableScroll from "../../utils/disable-scroll"

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
    getRoleOptions(user) {
      return [
        {
          label: "Admin",
          onClick: () => {
            this.selectedUser.role = "Admin"
            this.$resources.updateUserRole.submit({
              user_id: this.selectedUser?.user_name,
              user_role: "Drive " + this.selectedUser?.role,
            })
          },
          enabled: user.role !== "Admin",
        },
        {
          label: "User",
          enabled: user.role !== "User",
          onClick: () => {
            this.selectedUser.role = "User"
            this.$resources.updateUserRole.submit({
              user_id: this.selectedUser?.user_name,
              user_role: "Drive " + this.selectedUser?.role,
            })
          },
        },
        {
          label: "Guest",
          enabled: user.role !== "Guest",
          onClick: () => {
            this.selectedUser.role = "Guest"
            this.$resources.updateUserRole.submit({
              user_id: this.selectedUser?.user_name,
              user_role: "Drive " + this.selectedUser?.role,
            })
          },
        },
        {
          label: "Remove",
          class: "text-red-500",
          enabled: false,
          component: (props) =>
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
          onClick: () => {
            console.log("User has been removed")
          },
        },
      ].filter((item) => item.enabled)
    },
    viewGroupDetails(value) {
      this.activeGroup = value
      this.RoleName = value
      this.EditRoleDialog = !this.EditRoleDialog
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
    fetchAllUsers: {
      url: "drive.utils.users.get_users_with_drive_user_role",
      params: {
        get_roles: true,
      },
      method: "GET",
      auto: true,
      onSuccess(data) {
        // Update group key to filter
        data.forEach(function (item) {
          if (item.email) {
            item.user_name = item.email
            item.user_type = "User"
            delete item.email
          }
        })
      },
      onError(error) {
        if (error.messages) {
          this.errorMessage = error.messages.join("\n")
        } else {
          this.errorMessage = error.message
        }
      },
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
    updateUserRole: {
      url: "drive.utils.users.add_drive_user_role",
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
  },
}
</script>
