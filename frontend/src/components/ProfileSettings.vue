<template>
  <div
    class="flex h-full w-full flex-col items-start justify-start rounded-lg text-center">
    <h1 class="font-semibold">My Profile</h1>
    <span class="text-sm py-1 mb-4 text-gray-600">
      Manage your profile and preferences
    </span>
    <span class="text-base font-medium text-gray-700 mb-2">Profile</span>
    <div class="flex justify-start w-full items-center gap-2">
      <Avatar size="3xl" :image="imageURL" :label="fullName" class="mr-8" />
      <Input v-model="fullName" iconLeft="edit-2" />
    </div>
    <hr class="w-full mt-6 mb-4 border-1" />
    <span class="text-base font-medium text-gray-700 mb-2">Preferences</span>
    <div class="flex items-center justify-between w-full mb-2">
      <div class="flex flex-col items-start justify-center w-full">
        <span class="text-gray-900 text-base mb-1">
          Sort folders before files
        </span>
        <span class="text-gray-700 text-sm">
          Always show folders before files while respecting the sort for each
        </span>
      </div>
      <Switch />
    </div>
    <div class="flex items-center justify-between w-full my-2">
      <div class="flex flex-col items-start justify-center w-full">
        <span class="text-gray-900 text-base mb-1">Start page</span>
        <span class="text-gray-700 text-sm">
          Change the default start page to your liking
        </span>
      </div>
      <Dropdown placement="right" :options="routeOptions">
        <Button variant="subtle">Home</Button>
      </Dropdown>
    </div>
    <!--     <div class="flex items-center justify-between w-full  my-2">
    <div class="flex flex-col items-start justify-center w-full">
      <span class="text-gray-900 text-base mb-1">Don't remember me</span>
      <span class="text-gray-700 text-sm">Always log you out on closing Frappe Drive</span>
    </div>
      <Switch />
    </div> -->
  </div>
</template>
<script>
import { Button, Checkbox, Input, Switch, Dropdown, Avatar } from "frappe-ui";

export default {
  name: "NoFilesSection",
  components: { Avatar, Button, Input, Checkbox, Switch, Dropdown },
  data() {
    return {
      fullName: this.$store.state.user.fullName,
      routeOptions: [
        {
          group: "Routes",
          hideLabel: true,
          items: [
            {
              icon: "home",
              label: "Home",
            },
            {
              icon: "clock",
              label: "Recents",
            },
            {
              icon: "star",
              label: "Favourites",
            },
            {
              icon: "users",
              label: "Shared",
            },
            {
              icon: "trash-2",
              label: "Trash",
            },
          ],
        },
      ],
    };
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded;
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ");
    },
    /* fullName() {
      return this.$store.state.user.fullName;
    }, */
    imageURL() {
      return this.$store.state.user.imageURL;
    },
  },
};
</script>
