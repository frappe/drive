<template>
  <Dialog v-model="open" :options="{ title: roleName, size: 'lg' }">
    <template #body-content>
      <label class="block text-base text-gray-600 my-2">Add User</label>
      <UserSearch
        :button-variant="'solid'"
        :search-groups="false"
        :active-users="uniqueUsers"
        :active-groups="[]"
        @add-new-users="(data) => addUser(data.users)"
      />
      <label
        v-if="UsersInRole.length"
        class="block text-base text-gray-600 mt-6 mb-2"
      >
        Users in this Group
      </label>
      <div
        v-for="(user, index) in uniqueUsers"
        :key="user.user_name"
        class="flex flex-row w-full gap-2 items-center rounded py-2 px-1"
      >
        <Avatar :image="user.user_image" :label="user.full_name" size="xl" />
        <div>
          <p class="text-gray-900 text-base font-medium">
            {{ user.full_name }}
          </p>
          <p class="text-gray-600 text-base">
            {{ user.user_name }}
          </p>
        </div>
        <Button class="ml-auto" @click="removeUser(user)">Remove</Button>
      </div>
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
  </Dialog>
</template>
<script>
import {
  Input,
  Avatar,
  Dialog,
  ErrorMessage,
  Button,
  Tooltip,
  FeatherIcon,
} from "frappe-ui"
import UserSearch from "./ShareDialog/UserSearch.vue"

export default {
  name: "RoleDetailsDialog",
  components: {
    Avatar,
    Dialog,
    UserSearch,
    ErrorMessage,
    Button,
    Input,
    Tooltip,
    FeatherIcon,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    roleName: {
      type: String,
      default: null,
      required: true,
    },
  },
  emits: ["update:modelValue", "success"],
  data() {
    return {
      NewRoleName: "",
      UsersInRole: [],
      NewUsersInRole: [],
      errorMessage: "",
    }
  },
  computed: {
    uniqueUsers() {
      return this.removeDuplicateObjects(this.UsersInRole, "user_name")
    },
    uniqueEmails() {
      const uniqueUsernames = new Set()
      this.NewUsersInRole.forEach((user) => {
        uniqueUsernames.add(user)
      })
      this.UsersInRole.forEach((user) => {
        uniqueUsernames.add(user.user_name)
      })
      return Array.from(uniqueUsernames)
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
        if (!value) {
          this.newName = ""
          this.errorMessage = ""
        }
      },
    },
  },
  methods: {
    addUser(value) {
      value.forEach((user) => {
        this.UsersInRole.push(user)
        this.NewUsersInRole.push(user.user_name)
      })
      this.$resources.addUsersToGroup.submit()
    },
    removeDuplicateObjects(arr, property) {
      return [...new Map(arr.map((obj) => [obj[property], obj])).values()]
    },
    removeUser(user, index) {
      this.$resources.RemoveUsersFromGroup.submit({
        group_name: this.roleName,
        user_emails: [user.user_name],
      })
    },
  },
  resources: {
    getUsersInGroup() {
      return {
        url: "drive.utils.user_group.get_users_in_group",
        params: {
          group_name: this.roleName,
        },
        onSuccess(data) {
          this.UsersInRole = data
          data.forEach((user) => {
            user.user_name = user.email
            user.user_type = "User"
            delete user.name
          })
        },
        onError(data) {
          console.log(data)
        },
        auto: true,
      }
    },
    addUsersToGroup() {
      return {
        url: "drive.utils.user_group.add_users_to_group",
        params: {
          group_name: this.roleName,
          user_emails: this.NewUsersInRole,
        },
        validate: () => {
          if (!this.uniqueEmails.length) {
            this.errorMessage = "Group needs atleast one member"
          }
        },
        onSuccess(data) {
          this.errorMessage = ""
          this.$emit("success", data)
        },
        onError(data) {
          console.log(data)
          this.errorMessage = data
        },
        auto: false,
      }
    },
    RemoveUsersFromGroup() {
      return {
        url: "drive.utils.user_group.remove_users_from_group",
        params: {
          group_name: this.roleName,
          user_emails: null,
        },
        validate: () => {
          if (this.uniqueEmails.length === 1) {
            this.errorMessage = "Group needs atleast one active member"
          }
        },
        onSuccess() {
          this.errorMessage = ""
          this.$resources.getUsersInGroup.fetch()
        },
        onError(data) {
          if (data.messages === "Data missing in table: User Group Members'") {
            this.errorMessage = "Group needs atleast one active member"
          }
        },
        auto: false,
      }
    },
  },
}
</script>
