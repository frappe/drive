<template class="bg-gray-200">
  <UserDropdown />
  <div ondragstart="return false;" ondrop="return false;" class="my-2">
    <router-link
      v-for="item in sidebarItems"
      :key="item.label"
      v-slot="{ href, navigate }"
      :to="item.route">
      <a
        :class="[
          item.highlight() ? 'bg-white shadow-sm' : ' hover:bg-gray-100',
        ]"
        :href="href"
        class="flex items-center text-gray-800 text-sm w-full mb-0.5 h-7 px-3 py-1 gap-3 rounded focus:outline-none transition"
        @click="navigate && $emit('toggleMobileSidebar')">
        <FeatherIcon
          :name="item.icon"
          class="stroke-1.5 w-4 h-4 text-gray-800" />
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
          route: "/home",
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
          label: "Shared",
          route: "/shared",
          icon: "users",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Shared";
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
        auto: false,
      };
    },
  },
};
</script>
