<template>
  <div
    class="flex h-full w-full flex-col items-start justify-start rounded-lg text-center">
    <h1 class="font-semibold mb-1 text-xl">User Groups</h1>
    <span class="text-sm py-1 mb-8 text-gray-600">
      Create and manage user groups
    </span>
    <!-- <span class="text-lg font-medium">Organization Settings</span>
    <div class="flex justify-between w-full pt-4 pb-8">
      <div class="flex flex-col items-start">
        <span class="text-base font-medium">Name</span>
        <span class="text-sm py-1 text-gray-600">
          All Drive users on this instance are a part of this
        </span>
      </div>
      <Button class="font-medium text-gray-800" appearance="minimal">
        <template #prefix>
          <FeatherIcon name="edit" class="text-gray-800 stroke-1.5 h-4" />
        </template>
        Frappe
      </Button>
    </div> -->
    <div class="flex items-center w-full mb-1">
      <span class="text-base font-medium">Groups</span>
      <Button
        variant="solid"
        icon-left="plus"
        class="ml-auto"
        @click="CreateRoleDialog = !CreateRoleDialog">
        New
      </Button>
    </div>

    <div
      class="flex flex-col h-full w-full overflow-x-hidden overflow-y-scroll">
      <div
        @click="viewGroupDetails(group.name)"
        v-for="group in AllRoles"
        :key="group.name"
        class="flex flex-col items-start content-center items-start w-full hover:bg-gray-50 rounded cursor-pointer group">
        <div class="flex items-center w-full py-4 px-1">
          <Avatar size="xl" :label="group.name" />
          <span class="ml-2 text-base text-gray-900">{{ group.name }}</span>
          <Button
            icon="trash-2"
            variant="minimal"
            class="z-40 text-red-500 ml-auto invisible group-hover:visible"
            v-on:click.native.stop="
              $resources.deleteUserGroup.submit({
                group_name: group.name,
              })
            ">
            Delete
          </Button>
        </div>
        <div class="mx-3 h-px border-t border-gray-200 w-full"></div>
      </div>
    </div>
    <!-- <div v-else class="h-full w-full flex flex-col items-center justify-center">
      <FeatherIcon class="h-10 stroke-1 text-gray-600" name="users" />
      <span class="text-gray-800 text-sm">You dont have any roles</span>
      <span class="text-gray-700 text-xs">Create a new role</span>
    </div> -->
    <span class="text-xs pb-4 text-gray-600 mt-auto">
      This page is only available to Administrators
    </span>
  </div>
  <NewRoleDialog
    v-if="CreateRoleDialog"
    v-model="CreateRoleDialog"
    @success="
      () => {
        CreateRoleDialog = false;
        $resources.getUserGroups.fetch();
      }
    " />
  <RoleDetailsDialog
    v-if="EditRoleDialog"
    v-model="EditRoleDialog"
    :role-name="RoleName"
    @success="
      () => {
        EditRoleDialog = false;
        $resources.getUserGroups.fetch();
      }
    " />
</template>
<script>
import { Avatar, FeatherIcon, Input } from "frappe-ui";
import RoleDetailsDialog from "@/components/RoleDetailsDialog.vue";
import NewRoleDialog from "./NewRoleDialog.vue";
import { Building } from "lucide-vue-next";
import { Building2 } from "lucide-vue-next";

export default {
  name: "UserRoleSettings",
  components: {
    Input,
    Avatar,
    RoleDetailsDialog,
    NewRoleDialog,
    FeatherIcon,
    Building,
    Building2,
  },
  data() {
    return {
      RoleName: "",
      UsersInRole: [],
      CreateRoleDialog: false,
      EditRoleDialog: false,
      AllRoles: null,
      errorMessage: "",
    };
  },
  computed: {
    memberEmails() {
      let x = [];
      this.UsersInRole.forEach((user) => x.push(user.email));
      return x;
    },
  },
  methods: {
    viewGroupDetails(value) {
      this.RoleName = value;
      this.EditRoleDialog = !this.EditRoleDialog;
    },
  },
  resources: {
    deleteUserGroup() {
      return {
        url: "drive.utils.user_group.delete_user_group",
        params: {
          group_name: null,
        },
        onSuccess() {
          this.errorMessage = "";
          this.$resources.getUserGroups.fetch();
        },
        onError(data) {
          console.log(data);
          this.errorMessage = data;
        },
        auto: false,
      };
    },
    getUserGroups() {
      return {
        url: "drive.utils.user_group.get_name_of_all_user_groups",
        onSuccess(data) {
          this.AllRoles = data;
        },
        onError(data) {
          console.log(data);
        },
        auto: true,
      };
    },
  },
};
</script>
