<template>
  <h1 class="font-semibold mb-4">Users</h1>
  <div class="flex flex-col items-stretch justify-start overflow-y-auto">
    <div class="flex items-center justify-between">
      <!-- <Button
        variant="subtle"
        icon-left="plus"
        @click="CreateRoleDialog = !CreateRoleDialog"
      >
        Invite
      </Button> -->
    </div>
    <div
      v-for="(user, index) in $resources.fetchAllUsers?.data"
      :key="user.user_name"
    >
      <div
        v-if="index > 0"
        class="w-[95%] mx-auto h-px border-t border-gray-200"
      ></div>
      <div class="flex items-center justify-start py-2 pl-2 pr-4 gap-x-2">
        <Avatar :image="user.user_image" :label="user.full_name" size="lg" />
        <div class="flex flex-col">
          <span class="text-base">{{ user.full_name }}</span>
          <span class="text-base text-gray-700">{{ user.user_name }}</span>
        </div>
        <span class="ml-auto text-base text-gray-600">{{ user.role }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { Avatar, FeatherIcon, Dropdown, Dialog } from "frappe-ui"
import RoleDetailsDialog from "@/components/RoleDetailsDialog.vue"
import NewRoleDialog from "./NewRoleDialog.vue"

export default {
  name: "UserRoleSettings",
  components: {
    Avatar,
    RoleDetailsDialog,
    NewRoleDialog,
    FeatherIcon,
    Dropdown,
    Dialog,
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
  },
}
</script>
