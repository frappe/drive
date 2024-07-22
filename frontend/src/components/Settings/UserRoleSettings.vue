<template>
  <div class="flex items-center mb-2">
    <h1 class="font-semibold">Groups</h1>
    <Button
      variant="subtle"
      icon-left="plus"
      class="ml-auto"
      @click="CreateRoleDialog = !CreateRoleDialog"
    >
      Create
    </Button>
  </div>
  <div
    class="w-full h-full flex flex-col items-stretch justify-start overflow-y-auto"
  >
    <div v-for="(group, index) in AllRoles" :key="group.name">
      <div
        v-if="index > 0"
        class="w-[95%] mx-auto h-px border-t border-gray-200"
      ></div>
      <div
        class="flex text-base items-center justify-start p-2 cursor-pointer hover:bg-gray-50 rounded w-full"
        @click.self="viewGroupDetails(group.name)"
      >
        <Avatar size="lg" :label="group.name" />
        <span class="ml-2">{{ group.name }}</span>
        <Dropdown
          v-if="isDriveadmin"
          :button="{
            icon: 'more-horizontal',
            label: 'Page Options',
            variant: 'ghost',
          }"
          class="ml-auto"
          placement="right"
          :options="[
            {
              label: 'Delete',
              icon: 'trash-2',
              onClick: () => {
                activeGroup = group.name
                showDeleteDialog = true
              },
            },
          ]"
        >
          <Button>
            <template #icon>
              <FeatherIcon name="more-horizontal" class="h-4 w-4" />
            </template> </Button
        ></Dropdown>
      </div>
    </div>

    <div
      v-if="!AllRoles?.length"
      class="h-1/2 w-full flex flex-col items-center justify-center my-auto"
    >
      <FeatherIcon class="h-8 stroke-1 text-gray-600" name="users" />
      <span class="text-gray-800 text-sm mt-2">No groups</span>
    </div>

    <NewRoleDialog
      v-if="CreateRoleDialog"
      v-model="CreateRoleDialog"
      @success="
        () => {
          CreateRoleDialog = false
          $resources.getUserGroups.fetch()
        }
      "
    />
    <RoleDetailsDialog
      v-if="EditRoleDialog"
      v-model="EditRoleDialog"
      :role-name="RoleName"
      @success="
        () => {
          $resources.getUserGroups.fetch()
        }
      "
    />
    <Dialog
      v-model="showDeleteDialog"
      :options="{
        title: 'Delete ' + activeGroup,
        message:
          'This will delete the group. Members will lose access to files shared with this group.',
        size: 'sm',
        actions: [
          {
            label: 'Confirm',
            variant: 'solid',
            theme: 'red',
            onClick: () => {
              $resources.deleteUserGroup.submit({
                group_name: activeGroup,
              })
            },
          },
        ],
      }"
    />
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
    isDriveadmin() {
      return this.$store.state.user.driveAdmin
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
    deleteUserGroup() {
      return {
        url: "drive.utils.user_group.delete_user_group",
        params: {
          group_name: null,
        },
        onSuccess() {
          this.errorMessage = ""
          this.activeGroup = ""
          this.showDeleteDialog = false
          this.$resources.getUserGroups.fetch()
        },
        onError(data) {
          console.log(data)
          this.errorMessage = data
        },
        auto: false,
      }
    },
    getUserGroups() {
      return {
        url: "drive.utils.user_group.get_name_of_all_user_groups",
        onSuccess(data) {
          this.AllRoles = data
        },
        onError(data) {
          console.log(data)
        },
        auto: true,
      }
    },
  },
}
</script>
