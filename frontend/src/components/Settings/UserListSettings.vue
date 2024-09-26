<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold">Users</h1>
    <Button
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
        <span class="ml-auto text-base text-gray-600">{{ user.role }}</span>
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
      actions: [
        {
          label: 'Send Invitation',
          variant: 'solid',
          disabled: !emailsToInvite.length,
          loading: $resources.inviteUsers.loading,
          onClick: () => {
            $resources.inviteUsers.submit({ emails: emailsToInvite.join(',') })
            showInviteUserDialog = false
          },
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-wrap gap-1 rounded bg-gray-100 p-0.5">
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
      </div>
    </template>
  </Dialog>
</template>

<script>
import { Avatar, FeatherIcon, Dropdown, Dialog } from "frappe-ui"
import RoleDetailsDialog from "@/components/RoleDetailsDialog.vue"
import NewRoleDialog from "./NewRoleDialog.vue"
import { PlusIcon, SearchIcon, XIcon } from "lucide-vue-next"

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
  },
  data() {
    return {
      RoleName: "",
      UsersInRole: [],
      CreateRoleDialog: false,
      EditRoleDialog: false,
      AllRoles: null,
      errorMessage: "",
      activeGroup: null,
      showDeleteDialog: false,
      showInviteUserDialog: false,
      emailsToInvite: "",
      emailsTxt: "",
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
      onSuccess(data) {
        console.log(data)
      },
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
