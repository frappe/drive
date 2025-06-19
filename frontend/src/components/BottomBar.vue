<template>
  <div class="border-r bg-surface-menu-bar transition-all">
    <div
      ondragstart="return false;"
      ondrop="return false;"
      class="grid grid-cols-6 h-14 items-center border-y border-outline-gray-2 standalone:pb-4 px-1"
    >
      <router-link
        v-for="item in sidebarItems"
        :key="item.label"
        v-slot="{ href, navigate }"
        :to="item.route"
      >
        <a
          class="flex flex-col items-center justify-center py-3 transition active:scale-95 rounded"
          :class="[
            item.highlight()
              ? 'bg-surface-white shadow-sm border-[0.5px] border-outline-gray-2'
              : ' hover:bg-surface-gray-2',
          ]"
          :href="href"
          @click="navigate && $emit('toggleMobileSidebar')"
        >
          <component
            :is="item.icon"
            class="stroke-1.5 self-center w-auto h-5.5 text-ink-gray-8"
          />
        </a>
      </router-link>
    </div>
  </div>
</template>
<script>
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideClock from "~icons/lucide/clock"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
import LucideTrash from "~icons/lucide/trash"
import LucideUsers from "~icons/lucide/users"

export default {
  name: "Sidebar",
  emits: ["toggleMobileSidebar"],
  data() {
    return {
      sidebarResizing: false,
    }
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    team() {
      return this.$route.params.team || localStorage.getItem("recentTeam")
    },
    sidebarItems() {
      return [
        // {
        //   label: "Search",
        //   route: () => {},
        //   icon: "search",
        //   highlight: () => {},
        // },
        {
          label: "Home",
          route: "/t/" + this.team,
          icon: LucideHome,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Home"
          },
        },
        {
          label: "Recents",
          route: "/t/" + this.team + "/recents",
          icon: LucideClock,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Recents"
          },
        },
        {
          label: "Favourites",
          route: "/t/" + this.team + "/favourites",
          icon: LucideStar,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Favourites"
          },
        },
        {
          label: "Team",
          route: "/t/" + this.team + "/team",
          icon: LucideBuilding2,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Team"
          },
        },
        {
          label: "Shared",
          route: "/shared",
          icon: LucideUsers,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Shared"
          },
        },
        {
          label: "Trash",
          route: "/t/" + this.team + "/trash",
          icon: LucideTrash,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Trash"
          },
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
    startResize() {
      document.addEventListener("mousemove", this.resize)
      document.addEventListener("mouseup", () => {
        document.body.classList.remove("select-none")
        document.body.classList.remove("cursor-col-resize")
        this.sidebarResizing = false
        document.removeEventListener("mousemove", this.resize)
      })
    },
    resize(e) {
      this.sidebarResizing = true
      document.body.classList.add("select-none")
      document.body.classList.add("cursor-col-resize")
      let sidebarWidth = e.clientX
      let range = [60, 180]
      if (sidebarWidth > range[0] && sidebarWidth < range[1]) {
        sidebarWidth = 60
        this.$store.commit("setIsSidebarExpanded", false)
      }
      if (sidebarWidth > 180) {
        this.$store.commit("setIsSidebarExpanded", true)
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
        // BROKEN
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
