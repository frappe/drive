<template>
  <Dialog v-model="open" :options="{ title: 'New Group', size: 'lg' }">
    <template #body-content>
      <label class="block text-sm text-gray-600 mb-2">Group Name</label>
      <Input v-model="roleName" placeholder="Group Name" type="text" />
      <ErrorMessage class="text-sm mt-2" :message="groupNameError" />
      <label class="block text-sm text-gray-600 mt-4 mb-1">Add User</label>
      <UserSearch
        :search-groups="false"
        :active-users="uniqueUsers"
        :active-groups="[]"
        @add-new-users="(data) => addUser(data.users)"
      />
      <ErrorMessage class="text-sm mt-2" :message="memberError" />
      <label v-if="UsersInRole.length" class="block text-sm text-gray-600 mt-6">
        Users in this Group
      </label>
      <div
        v-for="(user, index) in uniqueUsers"
        :key="user.user_name"
        class="mt-1 flex flex-row w-full gap-2 items-center hover:bg-gray-50 rounded py-2 px-1 cursor-pointer group"
      >
        <Avatar :image="user.user_image" :label="user.full_name" size="xl" />
        <div>
          <p class="text-gray-900 text-sm font-medium">
            {{ user.full_name }}
          </p>
          <p class="text-gray-600 text-sm">
            {{ user.user_name }}
          </p>
        </div>
        <Button class="ml-auto" @click="UsersInRole.splice(index, 1)"
          >Remove</Button
        >
      </div>
      <div class="flex mt-6">
        <Button
          variant="solid"
          class="w-full"
          @click="$resources.createUserGroup.submit"
        >
          Create
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import {
  Avatar,
  Dialog,
  ErrorMessage,
  Input,
  Button,
  Tooltip,
  FeatherIcon,
} from "frappe-ui"
import UserSearch from "@/components/ShareDialog/UserSearch.vue"

export default {
  name: "RoleDetailsDialog",
  components: {
    Avatar,
    Dialog,
    UserSearch,
    ErrorMessage,
    Button,
    Input,
    FeatherIcon,
    Tooltip,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["update:modelValue", "success"],
  data() {
    return {
      roleName: "",
      UsersInRole: [],
      groupNameError: [],
      memberError: [],
      errorMessage: "",
    }
  },
  computed: {
    uniqueEmails() {
      const uniqueUsernames = new Set()
      this.UsersInRole.forEach((user) => {
        uniqueUsernames.add(user.user_name)
      })
      return Array.from(uniqueUsernames)
    },
    uniqueUsers() {
      return this.removeDuplicateObjects(this.UsersInRole, "user_name")
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
    addUser(data) {
      data.forEach((user) => {
        this.memberError = ""
        this.UsersInRole.push(user)
      })
    },
    removeDuplicateObjects(arr, property) {
      return [...new Map(arr.map((obj) => [obj[property], obj])).values()]
    },
  },
  resources: {
    createUserGroup() {
      return {
        url: "drive.utils.user_group.create_user_group",
        params: {
          group_name: this.roleName,
          members: this.uniqueEmails,
        },
        validate: () => {
          if (!this.roleName.length) {
            this.groupNameError = "Group name is required"
          }
          if (!this.uniqueEmails.length) {
            this.memberError = "Group needs atleast one member"
          }
        },
        onSuccess(data) {
          if (data.error) {
            this.groupNameError = data.message
          }
          this.$emit("success", data)
        },
        onError(data) {
          console.log(data.messages)
          if (data.messages === "Please set the document name") {
            this.groupNameError = "Group name is required"
          }
        },
        auto: false,
      }
    },
  },
}
</script>
