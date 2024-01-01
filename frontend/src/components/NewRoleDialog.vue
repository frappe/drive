<template>
  <Dialog v-model="open" :options="{ title: 'New Group Name', size: 'xs' }">
    <template #body-content>
      <label class="block text-xs text-gray-600 mt-2 mb-1">Group Name</label>
      <Input v-model="roleName" type="text" />
      <label class="block text-xs text-gray-600 mt-2 mb-1">Add User</label>
      <UserSearch
        :search-groups="false"
        class="mb-4"
        @submit="(user) => addUser(user)" />
      <label v-if="UsersInRole.length" class="block text-xs text-gray-600 mt-2">
        Users in this Group
      </label>
      <div
        v-for="user in uniqueUsers"
        :key="user.email"
        class="mt-1 flex flex-row w-full gap-2 items-center hover:bg-gray-50 rounded py-2 px-1 cursor-pointer group">
        <Avatar :image="user.user_image" :label="user.full_name" size="xl" />
        <div>
          <p class="text-gray-900 text-sm font-medium">
            {{ user.full_name }}
          </p>
          <p class="text-gray-600 text-sm">
            {{ user.email }}
          </p>
        </div>
        <Button
          class="ml-auto text-red-500 invisible group-hover:visible"
          variant="minimal"
          icon="trash-2" />
      </div>
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-6">
        <Button
          variant="solid"
          class="w-full"
          @click="$resources.createUserGroup.submit">
          Create
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Avatar, Dialog, ErrorMessage, Input, Button } from "frappe-ui";
import UserSearch from "./UserSearch.vue";

export default {
  name: "RoleDetailsDialog",
  components: { Avatar, Dialog, UserSearch, ErrorMessage, Button, Input },
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
      memberEmails: [],
      errorMessage: "",
    };
  },
  computed: {
    uniqueUsers() {
      return this.removeDuplicateObjects(this.UsersInRole, "email");
    },
    uniqueMemberEmails() {
      return [...new Set(this.memberEmails)];
    },
    open: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
        if (!value) {
          this.newName = "";
          this.errorMessage = "";
        }
      },
    },
  },
  methods: {
    addUser(value) {
      console.log(value);
      this.UsersInRole.push(value);
      this.memberEmails.push(value.email);
    },
    removeDuplicateObjects(arr, property) {
      return [...new Map(arr.map((obj) => [obj[property], obj])).values()];
    },
  },
  resources: {
    createUserGroup() {
      return {
        url: "drive.utils.user_group.create_user_group",
        params: {
          group_name: this.roleName,
          members: this.uniqueMemberEmails,
        },
        validate: () => {
          if (!this.memberEmails.length) {
            this.errorMessage = "Group needs atleast one member";
          }
        },
        onSuccess(data) {
          this.errorMessage = "";
          this.$emit("success", data);
        },
        onError(data) {
          console.log(data);
          this.errorMessage = data;
        },
        auto: false,
      };
    },
  },
};
</script>
