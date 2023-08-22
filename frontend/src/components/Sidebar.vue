<template class="bg-gray-200">
  <UserDropdown />
  <div
    ondragstart="return false;"
    ondrop="return false;"
    class="flex flex-col justify-between">
    <router-link
      v-for="item in sidebarItems"
      :key="item.label"
      v-slot="{ href, navigate }"
      :to="item.route">
      <a
        :class="[
          item.highlight() ? 'bg-white shadow-sm ' : ' hover:bg-gray-100',
        ]"
        :href="href"
        class="text-gray-700 text-sm w-full mb-0.5 h-7 px-2 py-1 gap-3 rounded focus:outline-none flex items-center"
        @click="navigate && $emit('toggleMobileSidebar')">
        <FeatherIcon :name="item.icon" class="text-gray-600 stroke-2 w-4 h-4" />
        {{ item.label }}
      </a>
    </router-link>
    <!-- <span
      class="w-[256px] h-7 px-3 py-4 gap-3 mt-auto rounded-lg focus:outline-none flex items-center">
      <FeatherIcon name="cloud" class="stroke-1.5 w-4 h-4" />
      Used :
      {{ $resources.getRootFolderSize.data + "B" }}
    </span> -->
  </div>
</template>
<script>
import UserDropdown from "@/components/UserDropdown.vue";
import { FeatherIcon } from "frappe-ui";

export default {
  name: "Sidebar",
  components: { FeatherIcon, UserDropdown },
  emits: ["toggleMobileSidebar"],
  computed: {
    sidebarItems() {
      return [
        /* {
          label: "Search",
          route: () => {},
          icon: "search",
          highlight: () => {},
        }, */
        {
          label: "Home",
          route: "/",
          icon: "home",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Home";
          },
        },
        {
          label: "Recents",
          route: "/recent",
          icon: "clock",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Recents";
          },
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: "star",
          highlight: () => {
            return (
              this.$store.state.currentBreadcrumbs[0].label === "Favourites"
            );
          },
        },
        {
          label: "Shared With Me",
          route: "/shared",
          icon: "share-2",
          highlight: () => {
            return (
              this.$store.state.currentBreadcrumbs[0].label === "Shared With Me"
            );
          },
        },
        {
          label: "Trash",
          route: "/trash",
          icon: "trash-2",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Trash";
          },
        },
      ];
    },
  },
  resources: {
    getRootFolderSize() {
      return {
        url: "drive.api.files.get_user_directory_size",
        onError(error) {
          console.log(error);
        },
        auto: true,
      };
    },
  },
};
</script>
