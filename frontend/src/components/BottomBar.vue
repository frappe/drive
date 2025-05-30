<template>
  <div class="border-r bg-gray-50 transition-all">
    <div
      ondragstart="return false;"
      ondrop="return false;"
      class="grid grid-cols-6 h-14 items-center border-y border-gray-300 standalone:pb-4 px-1"
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
              ? 'bg-white shadow-sm border-[0.5px] border-gray-300'
              : ' hover:bg-gray-100',
          ]"
          :href="href"
          @click="navigate && $emit('toggleMobileSidebar')"
        >
          <component
            :is="item.icon"
            class="stroke-1.5 self-center w-auto h-5.5 text-gray-800"
          />
        </a>
      </router-link>
      <!--  <span
        class="mt-auto w-[256px] h-7 px-3 py-4 gap-3 rounded-lg focus:outline-none flex items-center">
        <FeatherIcon name="cloud" class="stroke-1.5 w-4 h-4" />
        Used :
        {{ $resources.getRootFolderSize.data + "B" }}
      </span> -->
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui"
import Recent from "./EspressoIcons/Recent.vue"
import Star from "./EspressoIcons/Star.vue"
import Home from "./EspressoIcons/Home.vue"
import Trash from "./EspressoIcons/Trash.vue"
import Team from "./EspressoIcons/Organization.vue"
import Users from "./EspressoIcons/Users.vue"

export default {
  name: "Sidebar",
  components: { FeatherIcon },
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
          label: __("Home"),
          route: "/t/" + this.team,
          icon: Home,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Home"
          },
        },
        {
          label: __("Recents"),
          route: "/t/" + this.team + "/recents",
          icon: Recent,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Recents"
          },
        },
        {
          label: __("Favourites"),
          route: "/t/" + this.team + "/favourites",
          icon: Star,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Favourites"
          },
        },
        {
          label: __("Team"),
          route: "/t/" + this.team + "/team",
          icon: Team,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Team"
          },
        },
        {
          label: __("Shared"),
          route: "/shared",
          icon: Users,
          highlight: () => {
            return this.$store.state.breadcrumbs[0].name === "Shared"
          },
        },
        {
          label: __("Trash"),
          route: "/t/" + this.team + "/trash",
          icon: Trash,
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
