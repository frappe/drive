<template>
  <div class="border-r bg-gray-50 relative md:block">
    <div
      class="absolute right-0 z-10 h-full w-1 cursor-col-resize bg-gray-400 opacity-0 transition-opacity hover:opacity-100"
      :class="{ 'opacity-100': sidebarResizing }"
      @mousedown="startResize" />
    <div
      class="flex flex-col h-full p-2 transition-[width]"
      :class="!isExpanded ? 'items-center' : ''"
      :style="{ width: isExpanded ? '220px' : '50px' }">
      <PrimaryDropDown :is-expanded="isExpanded" />
      <div
        class="mt-2"
        :class="!isExpanded ? 'flex flex-col items-center' : ''"
        ondragstart="return false;"
        ondrop="return false;">
        <button
          class="flex items-center justify-start mb-0.5 hover:bg-gray-100 text-gray-800 text-sm w-full h-7 px-2.5 py-1 gap-2 rounded"
          @click="emitter.emit('showSearchPopup', true)">
          <FeatherIcon name="search" class="w-4.5 h-4.5" />
          <template v-if="isExpanded">
            <span>Search</span>
            <span
              v-if="currentPlatform === 'mac'"
              class="ml-auto text-sm text-gray-500">
              ⌘K
            </span>
            <span v-else class="ml-auto text-sm text-gray-500">Ctrl+K</span>
          </template>
        </button>
        <div v-for="item in sidebarItems" :key="item.label">
          <component
            :is="isExpanded ? 'div' : 'Tooltip'"
            :text="!isExpanded ? item.label : ''"
            placement="right">
            <router-link
              :to="item.route"
              class="flex items-center transition-all text-gray-800 text-sm mb-0.5 h-7 py-1 gap-2 rounded"
              :class="[
                item.highlight ? 'bg-white shadow-sm' : ' hover:bg-gray-100',
                isExpanded
                  ? 'w-full px-2.5 justify-start'
                  : 'w-7 px-1 justify-center',
              ]">
              <FeatherIcon
                :name="item.icon"
                class="w-4.5 h-4.5 text-gray-700"
                :stroke-width="1.5" />
              <span v-if="isExpanded">
                {{ item.label }}
              </span>
            </router-link>
          </component>
        </div>
      </div>
      <div class="mt-auto">
        <!-- <PrimaryDropDown /> -->
      </div>
    </div>
  </div>
</template>
<script>
import UserDropdown from "@/components/UserDropdown.vue";
import { FeatherIcon, Tooltip } from "frappe-ui";
import PrimaryDropDown from "./PrimaryDropdown.vue";

export default {
  name: "Sidebar",
  components: { FeatherIcon, UserDropdown, PrimaryDropDown, Tooltip },
  emits: ["toggleMobileSidebar", "showSearchPopUp"],
  data() {
    return {
      sidebarResizing: false,
    };
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded;
    },
    /* currentSideBarWidth: {
      get() {
        return this.currentSideBarWidth = this.$store.state.IsSidebarExpanded ? 280 : 60
      },
      set(val) {
        console.log(val)
        return this.currentSideBarWidth = val
      }
    }, */
    currentPlatform() {
      let ua = navigator.userAgent.toLowerCase();
      if (ua.indexOf("win") > -1) {
        return "win";
      } else if (ua.indexOf("mac") > -1) {
        return "mac";
      } else if (ua.indexOf("x11") > -1 || ua.indexOf("linux") > -1) {
        return "linux";
      }
      return "";
    },
    sidebarItems() {
      return [
        {
          label: "Home",
          route: "/home",
          icon: "home",
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Home",
        },
        {
          label: "Recents",
          route: "/recents",
          icon: "clock",
          highlight:
            this.$store.state.currentBreadcrumbs[0].label === "Recents",
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: "star",
          highlight:
            this.$store.state.currentBreadcrumbs[0].label === "Favourites",
        },
        {
          label: "Shared",
          route: "/shared",
          icon: "users",
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Shared",
        },
        {
          label: "Trash",
          route: "/trash",
          icon: "trash-2",
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Trash",
        },
      ];
    },
  },
  methods: {
    toggleExpanded() {
      return this.$store.commit(
        "setIsSidebarExpanded",
        this.isExpanded ? false : true
      );
    },
    startResize() {
      document.addEventListener("mousemove", this.resize);
      document.addEventListener("mouseup", () => {
        document.body.classList.remove("select-none");
        document.body.classList.remove("cursor-col-resize");
        this.sidebarResizing = false;
        document.removeEventListener("mousemove", this.resize);
      });
    },
    resize(e) {
      this.sidebarResizing = true;
      document.body.classList.add("select-none");
      document.body.classList.add("cursor-col-resize");
      let sidebarWidth = e.clientX;
      let range = [60, 180];
      if (sidebarWidth > range[0] && sidebarWidth < range[1]) {
        sidebarWidth = 60;
        this.$store.commit("setIsSidebarExpanded", false);
      }
      if (sidebarWidth > 180) {
        this.$store.commit("setIsSidebarExpanded", true);
      }
      /* if (sidebarWidth < 100) {
        this.$store.commit("setIsSidebarExpanded", false )
      }
      if (sidebarWidth > 100) {
        this.$store.commit("setIsSidebarExpanded", true )
      } */
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
