<template>
  <div class="border-r bg-gray-50 transition-all">
    <div
      ondragstart="return false;"
      ondrop="return false;"
      class="grid grid-cols-5 h-14 items-center border-y border-gray-300 standalone:pb-4 px-1"
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
          <FeatherIcon
            :name="item.icon"
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
    /* currentSideBarWidth: {
        get() {
          return this.currentSideBarWidth = this.$store.state.IsSidebarExpanded ? 280 : 60
        },
        set(val) {
          console.log(val)
          return this.currentSideBarWidth = val
        }
      }, */
    sidebarItems() {
      return [
        /*  {
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
            return this.$store.state.currentBreadcrumbs[0].label === "Home"
          },
        },
        {
          label: "Recents",
          route: "/recents",
          icon: "clock",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Recents"
          },
        },
        {
          label: "Favourites",
          route: "/favourites",
          icon: "star",
          highlight: () => {
            return (
              this.$store.state.currentBreadcrumbs[0].label === "Favourites"
            )
          },
        },
        {
          label: "Shared",
          route: "/shared",
          icon: "users",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Shared"
          },
        },
        {
          label: "Trash",
          route: "/trash",
          icon: "trash-2",
          highlight: () => {
            return this.$store.state.currentBreadcrumbs[0].label === "Trash"
          },
        },
      ]
    },
  },
  methods: {
    toggleExpanded() {
      console.log("test")
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
