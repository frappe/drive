<template>
  <div
    :class="isExpanded ? 'w-[220px]' : 'w-[50px]'"
    class="border-r bg-gray-50 relative hidden sm:flex h-full flex-col justify-start duration-300 ease-in-out p-2"
  >
    <PrimaryDropDown :is-expanded="isExpanded" />

    <div
      class="mt-2.5"
      :class="!isExpanded ? 'flex flex-col items-start' : ''"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <SidebarItem
        :label="'Search'"
        class="mb-0.5"
        :is-collapsed="!isExpanded"
        @click="() => emitter.emit('showSearchPopup', true)"
      >
        <template #icon>
          <Search
            class="stroke-[1.5] h-4 w-4 text-gray-700 focus:outline-none"
          />
        </template>
        <template #right>
          <div
            class="flex items-center justify-start w-full duration-300 ease-in-out"
            :class="
              isExpanded ? 'ml-2 opacity-100' : 'ml-0 overflow-hidden opacity-0'
            "
          >
            <span
              class="text-sm text-gray-500 ease-in"
              :class="
                isExpanded
                  ? 'opacity-100 ml-auto'
                  : 'ml-0 overflow-hidden opacity-0'
              "
            >
              {{ currentPlatform === "mac" ? "⌘K" : " Ctrl+K" }}
            </span>
          </div>
        </template>
      </SidebarItem>

      <SidebarItem
        v-for="item in sidebarItems"
        :key="item.label"
        :icon="item.icon"
        :label="item.label"
        :to="item.route"
        :is-collapsed="!isExpanded"
        class="mb-0.5"
      />
    </div>
    <SidebarItem
      :label="!isExpanded ? 'Expand' : 'Collapse'"
      :is-collapsed="!isExpanded"
      class="mt-auto"
      @click="toggleExpanded"
    >
      <template #icon>
        <span class="grid h-4.5 w-4.5 flex-shrink-0 place-items-center">
          <ArrowLeftFromLine
            class="stroke-[1.5] h-4 w-4 text-gray-700 duration-300 ease-in-out"
            :class="{ '[transform:rotateY(180deg)]': !isExpanded }"
          />
        </span>
      </template>
    </SidebarItem>
  </div>
</template>
<script>
import PrimaryDropDown from "./PrimaryDropdown.vue"
import { ArrowLeftFromLine } from "lucide-vue-next"
import Search from "./EspressoIcons/Search.vue"
import Recent from "./EspressoIcons/Recent.vue"
import Star from "./EspressoIcons/Star.vue"
import Users from "./EspressoIcons/Users.vue"
import Trash from "./EspressoIcons/Trash.vue"
import SidebarItem from "@/components/SidebarItem.vue"
import Home from "./EspressoIcons/Home.vue"

export default {
  name: "Sidebar",
  components: { PrimaryDropDown, ArrowLeftFromLine, SidebarItem, Search },
  emits: ["toggleMobileSidebar", "showSearchPopUp"],
  data() {
    return {
      sidebarResizing: false,
    }
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    currentPlatform() {
      let ua = navigator.userAgent.toLowerCase()
      if (ua.indexOf("win") > -1) {
        return "win"
      } else if (ua.indexOf("mac") > -1) {
        return "mac"
      } else if (ua.indexOf("x11") > -1 || ua.indexOf("linux") > -1) {
        return "linux"
      }
      return ""
    },
    sidebarItems() {
      return [
        {
          label: "Home",
          route: "/home",
          icon: Home,
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Home",
        },
        {
          label: "Recents",
          route: "/recents",
          icon: Recent,
          highlight:
            this.$store.state.currentBreadcrumbs[0].label === "Recents",
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: Star,
          highlight:
            this.$store.state.currentBreadcrumbs[0].label === "Favourites",
        },
        {
          label: "Shared",
          route: "/shared",
          icon: Users,
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Shared",
        },
        {
          label: "Trash",
          route: "/trash",
          icon: Trash,
          highlight: this.$store.state.currentBreadcrumbs[0].label === "Trash",
        },
      ]
    },
  },
  methods: {
    toggleExpanded() {
      return this.$store.commit(
        "setIsSidebarExpanded",
        this.isExpanded ? false : true
      )
    },
  },
  resources: {
    getRootFolderSize() {
      return {
        url: "drive.api.files.get_user_directory_size",
        onError(error) {
          console.log(error)
        },
        auto: false,
      }
    },
  },
}
</script>
