<template>
  <div
    :style="{ width: isExpanded ? '280px' : '60px' }"
    class="border-r bg-gray-50 transition-all relative md:block">
    <div
      class="absolute right-0 z-10 h-full w-1 cursor-col-resize bg-gray-400 opacity-0 transition-opacity hover:opacity-100"
      :class="{ 'opacity-100': sidebarResizing }"
      @mousedown="startResize" />
    <div class="py-1 flex flex-col justify-items-center h-full">
      <UserDropdown />
      <div ondragstart="return false;" ondrop="return false;" class="p-2.5">
        <div v-for="item in sidebarItems">
          <router-link
            v-if="item.route"
            :key="item.label"
            v-slot="{ href, navigate }"
            :to="item.route">
            <a
              class="sidebar-animate flex justify-start text-gray-800 text-sm w-full mb-1 h-7 px-2.5 gap-2 rounded focus:outline-none"
              :class="[
                item.highlight()
                  ? 'bg-white shadow-sm border-[0.5px] border-gray-300'
                  : ' hover:bg-gray-100',
              ]"
              :href="href"
              @click="navigate && $emit('toggleMobileSidebar')">
              <FeatherIcon
                :name="item.icon"
                class="stroke-1.5 self-center w-4 h-4 text-gray-800" />
              <span v-if="isExpanded" class="self-center">
                {{ item.label }}
              </span>
            </a>
          </router-link>
          <div v-else>
            <button
              @click="item.action"
              class="sidebar-animate flex justify-start text-gray-800 text-sm w-full mb-1 h-7 px-2.5 gap-2 rounded focus:outline-none"
              :class="[
                item.highlight()
                  ? 'bg-white shadow-sm border-[0.5px] border-gray-300'
                  : ' hover:bg-gray-100',
              ]">
              <FeatherIcon
                :name="item.icon"
                class="stroke-1.5 self-center w-4 h-4 text-gray-800" />
              <template v-if="isExpanded">
                <span class="self-center">{{ item.label }}</span>
                <span
                  class="ml-auto text-sm text-gray-500"
                  v-if="getPlatform === 'mac'">
                  ⌘K
                </span>
                <span class="ml-auto text-sm text-gray-500" v-else>Ctrl+K</span>
              </template>
            </button>
          </div>
        </div>
      </div>
      <div class="mt-auto">
        <PrimaryDropDown />
      </div>
    </div>
  </div>
</template>
<script>
import UserDropdown from "@/components/UserDropdown.vue";
import { FeatherIcon } from "frappe-ui";
import PrimaryDropDown from "./PrimaryDropdown.vue";

export default {
  name: "Sidebar",
  components: { FeatherIcon, UserDropdown, PrimaryDropDown },
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
    getPlatform() {
      let ua = navigator.userAgent.toLowerCase();
      if (ua.indexOf("win") > -1) {
        return "win";
      } else if (ua.indexOf("mac") > -1) {
        return "mac";
      } else if (ua.indexOf("x11") > -1 || ua.indexOf("linux") > -1) {
        return "linux";
      }
    },
    sidebarItems() {
      return [
        {
          label: "Search",
          action: () => this.emitter.emit("showSearchPopup", true),
          icon: "search",
          highlight: () => {},
        },
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
          route: "/recents",
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

<style scoped>
.sidebar-animate:active {
  transform: scaleX(0.985) scaleY(0.985) translateY(0.5px);
}
</style>
