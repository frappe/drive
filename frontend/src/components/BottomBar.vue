<template>
  <div
    class="grid grid-cols-5 bg-surface-modal border-t border-outline-gray-2 standalone:pb-4"
    :style="{
      gridTemplateColumns: `repeat(${sidebarItems.length}, minmax(0, 1fr))`,
    }"
  >
    <button
      v-for="tab in sidebarItems"
      :key="tab.label"
      class="flex flex-col items-center justify-center transition active:scale-95 h-[50px]"
      @click="$router.push(tab.route)"
    >
      <component
        :is="tab.icon"
        class="size-6"
        :class="[tab.highlight() ? 'text-ink-gray-8' : 'text-ink-gray-5']"
      />
    </button>
  </div>
</template>
<script>
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideClock from "~icons/lucide/clock"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
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
      return this.$store.state.sidebarCollapsed
    },
    team() {
      return this.$route.params.team || localStorage.getItem("recentTeam")
    },
    sidebarItems() {
      const first = this.$store.state.breadcrumbs[0] || {}
      return [
        {
          label: "Home",
          route: "/",
          icon: LucideHome,
          highlight: () => {
            return first.name === "Home"
          },
        },
        {
          label: "Team",
          route: "/teams",
          icon: LucideBuilding2,
          highlight: () => {
            return this.$route.name === "Teams"
          },
        },
        {
          label: "Recents",
          route: "/recents",
          icon: LucideClock,
          highlight: () => {
            return first.name === "Recents"
          },
        },

        {
          label: "Shared",
          route: "/shared",
          icon: LucideUsers,
          highlight: () => {
            return first.name === "Shared"
          },
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: LucideStar,
          highlight: () => {
            return first.name === "Favourites"
          },
        },
      ]
    },
  },
  methods: {
    toggleExpanded() {
      return this.$store.commit(
        "setSidebarCollapsed",
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
        this.$store.commit("setSidebarCollapsed", false)
      }
      if (sidebarWidth > 180) {
        this.$store.commit("setSidebarCollapsed", true)
      }
      /* if (sidebarWidth < 100) {
          this.$store.commit("setSidebarCollapsed", false )
        }
        if (sidebarWidth > 100) {
          this.$store.commit("setSidebarCollapsed", true )
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
