<template>
  <div
    :class="isExpanded ? 'w-[220px]' : 'w-[50px]'"
    class="border-r bg-gray-50 relative hidden sm:flex h-screen flex-col justify-start duration-300 ease-in-out p-2"
  >
    <PrimaryDropDown :is-expanded="isExpanded" />

    <div
      class="mt-2.5"
      :class="!isExpanded ? 'flex flex-col items-start' : ''"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <SidebarItem
        v-if="!isDriveGuest"
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
          ></div>
        </template>
      </SidebarItem>
      <SidebarItem
        v-if="!isDriveGuest"
        :label="'Notifications'"
        icon="inbox"
        class="mb-0.5"
        :is-collapsed="!isExpanded"
        :to="'/' + $route.params.team + '/notifications'"
      >
      </SidebarItem>
      <SidebarItem
        v-for="item in sidebarItems"
        :key="item.label"
        :icon="item.icon"
        :label="item.label"
        :to="item.route"
        @mouseenter="item.preload?.fetch?.({ team: $route.params.team })"
        :is-collapsed="!isExpanded"
        class="mb-0.5"
      />
    </div>
    <div class="mt-auto">
      <StorageBar v-if="!isDriveGuest" />
      <!-- <span>{{ $resources.getRootFolderSize.data }}</span> -->
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
  </div>
</template>
<script>
import { formatSize } from "../utils/format"
import PrimaryDropDown from "./PrimaryDropdown.vue"
import { ArrowLeftFromLine } from "lucide-vue-next"
import Search from "./EspressoIcons/Search.vue"
import Recent from "./EspressoIcons/Recent.vue"
import Star from "./EspressoIcons/Star.vue"
import MyDrive from "./EspressoIcons/MyDrive.vue"
import Users from "./EspressoIcons/Users.vue"
import Trash from "./EspressoIcons/Trash.vue"
import SidebarItem from "@/components/SidebarItem.vue"
import Home from "./EspressoIcons/Home.vue"
import StorageBar from "./StorageBar.vue"
import {
  getHome,
  getRecents,
  getFavourites,
  getPersonal,
  getTrash,
  getShared,
} from "@/resources/files"

export default {
  name: "Sidebar",
  components: {
    PrimaryDropDown,
    ArrowLeftFromLine,
    SidebarItem,
    Search,
    StorageBar,
  },
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
    isDriveGuest() {
      return this.$store.state.user.role === "Drive Guest"
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
          enabled: !this.isDriveGuest,
          label: "Home",
          route: `/${this.$route.params.team}/`,
          icon: Home,
          preload: getHome,
          highlight: this.$store.state.breadcrumbs[0].label === "Home",
        },
        {
          enabled: true,
          label: "My Space",
          route: `/${this.$route.params.team}/personal`,
          icon: MyDrive,
          preload: getPersonal,
          highlight: this.$store.state.breadcrumbs[0].label === "My Space",
        },
        {
          enabled: true,
          label: "Recents",
          route: `/${this.$route.params.team}/recents`,
          icon: Recent,
          preload: getRecents,
          highlight: this.$store.state.breadcrumbs[0].label === "Recents",
        },
        {
          enabled: true,
          label: "Favourites",
          route: `/${this.$route.params.team}/favourites`,
          icon: Star,
          preload: getFavourites,
          highlight: this.$store.state.breadcrumbs[0].label === "Favourites",
        },
        {
          enabled: true,
          label: "Shared",
          route: `/${this.$route.params.team}/shared`,
          preload: getShared,
          icon: Users,
          highlight: this.$store.state.breadcrumbs[0].label === "Shared",
        },
        {
          enabled: true,
          label: "Trash",
          route: `/${this.$route.params.team}/trash`,
          preload: getTrash,
          icon: Trash,
          highlight: this.$store.state.breadcrumbs[0].label === "Trash",
        },
      ].filter((item) => item.enabled)
    },
  },
  methods: {
    formatSize,
    toggleExpanded() {
      return this.$store.commit(
        "setIsSidebarExpanded",
        this.isExpanded ? false : true
      )
    },
  },
  resources: {
    getUnreadCount: {
      url: "drive.api.notifications.get_unread_count",
      auto: true,
      method: "GET",
      onSuccess(data) {
        this.$store.state.notifCount = data
      },
    },
  },
}
</script>
