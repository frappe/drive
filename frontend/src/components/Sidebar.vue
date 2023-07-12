<template class="bg-gray-50">
  <FrappeDriveLogo class="h-4 mb-8" />
  <div
    ondragstart="return false;"
    ondrop="return false;"
    class="flex flex-col justify-between">
    <div class="text-lg">
      <router-link
        v-for="item in sidebarItems"
        :key="item.label"
        v-slot="{ href, navigate }"
        :to="item.route">
        <a
          :class="[
            item.highlight()
              ? 'bg-gray-200 text-gray-900'
              : 'text-gray-800 hover:bg-gray-50',
          ]"
          :href="href"
          class="w-[224px] h-7 mb-1 px-3 py-4 gap-3 rounded-lg focus:outline-none flex items-center"
          @click="navigate && $emit('toggleMobileSidebar')">
          <FeatherIcon :name="item.icon" class="stroke-1.5 w-5 h-5" />
          {{ item.label }}
        </a>
      </router-link>
      <span
        class="w-[224px] h-7 mb-1 px-3 py-4 gap-3 mt-auto rounded-lg focus:outline-none flex items-center">
        <FeatherIcon name="cloud" class="stroke-1.5 w-5 h-5" />
        Used :
        {{ $resources.getRootFolderSize.data + "B" }}
      </span>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui";
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue";

export default {
  name: "Sidebar",
  components: { FeatherIcon, FrappeDriveLogo },
  emits: ["toggleMobileSidebar"],
  computed: {
    sidebarItems() {
      return [
        {
          label: "Home",
          route: "/",
          icon: "home",
          highlight: () => {
            if (this.$route.name === "Home") {
              return true;
            } else if (
              this.$store.state.currentBreadcrumbs[0].label === "Home" &&
              this.$route.name === "Folder"
            ) {
              return true;
            }
          },
        },
        {
          label: "Recents",
          route: "/recent",
          icon: "clock",
          highlight: () => {
            return this.$route.fullPath.endsWith("/recent");
          },
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: "star",
          highlight: () => {
            if (
              this.$store.state.currentBreadcrumbs[0].route === "/favourites" &&
              this.$route.name === "Folder"
            ) {
              return true;
            } else if (this.$route.name === "Favourites") {
              return true;
            }
          },
        },
        {
          label: "Shared With Me",
          route: "/shared",
          icon: "share-2",
          highlight: () => {
            if (
              this.$store.state.currentBreadcrumbs[0].route === "/shared" &&
              this.$route.name === "Folder"
            ) {
              return true;
            } else if (this.$route.name === "Shared") {
              return true;
            }
          },
        },
        {
          label: "Trash",
          route: "/trash",
          icon: "trash-2",
          highlight: () => {
            return this.$route.fullPath.endsWith("/trash");
          },
        },
        {
          label: "Workspace",
          route: "/workspace",
          icon: "tool",
          highlight: () => {
            return this.$route.fullPath.endsWith("/workspace");
          },
        },
      ];
    },
  },
  resources: {
    getRootFolderSize() {
      return {
        url: "drive.api.files.get_user_directory_size",
        onSuccess(data) {
          console.log(data);
        },
        onError(error) {
          console.log(error);
        },
        auto: true,
      };
    },
  },
};
</script>
