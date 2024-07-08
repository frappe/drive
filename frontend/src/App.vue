<template>
  <!-- Main container no scroll -->
  <div
    class="flex w-screen h-screen antialiased overflow-hidden"
    @contextmenu="handleDefaultContext($event)"
  >
    <!-- Main container with scroll -->
    <div class="h-full w-full flex flex-col">
      <SearchPopup
        v-if="isLoggedIn && showSearchPopup"
        v-model="showSearchPopup"
      />
      <div
        v-if="isLoggedIn || $route.meta.isHybridRoute"
        class="flex flex-col h-full overflow-hidden sm:flex-row"
      >
        <Sidebar v-if="isLoggedIn" class="hidden sm:block" />
        <div id="dropzoneElement" class="h-full w-full overflow-hidden">
          <Navbar
            :mobile-sidebar-is-open="showMobileSidebar"
            @toggle-mobile-sidebar="showMobileSidebar = !showMobileSidebar"
          />
          <div class="flex w-full h-full overflow-hidden">
            <!-- Find a better way to handle the height overflow here (52px is the Navbar) -->
            <div
              class="flex w-full h-[calc(100vh-88px)] sm:h-[calc(100vh-52px)] overflow-hidden"
            >
              <router-view :key="$route.fullPath" v-slot="{ Component }">
                <component :is="Component" id="currentPage" ref="currentPage" />
              </router-view>
            </div>
            <InfoSidebar v-if="hideInfoSideBar" />
          </div>
        </div>
        <BottomBar v-if="isLoggedIn" class="block sm:hidden" />
      </div>
      <!-- Auth -->
      <router-view v-else />
    </div>
  </div>
  <FileUploader v-if="isLoggedIn" />
  <Transition
    enter-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    enter-from-class="translate-y-1 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-1 opacity-0"
  >
    <UploadTracker v-if="showUploadTracker" />
  </Transition>
  <Toasts />
</template>
<script>
import Navbar from "@/components/Navbar.vue"
import Sidebar from "@/components/Sidebar.vue"
import InfoSidebar from "@/components/InfoSidebar.vue"
import MobileSidebar from "@/components/MobileSidebar.vue"
import UploadTracker from "@/components/UploadTracker.vue"
import { Button, FeatherIcon } from "frappe-ui"
import { Toasts } from "@/utils/toasts.js"
import FilePicker from "./components/FilePicker.vue"
import MoveDialog from "./components/MoveDialog.vue"
import SearchPopup from "./components/SearchPopup.vue"
import FileUploader from "./components/FileUploader.vue"
import BottomBar from "./components/BottomBar.vue"

export default {
  name: "App",
  components: {
    Navbar,
    Sidebar,
    InfoSidebar,
    MobileSidebar,
    UploadTracker,
    Button,
    FeatherIcon,
    Toasts,
    FilePicker,
    MoveDialog,
    SearchPopup,
    FileUploader,
    BottomBar,
  },
  data() {
    return {
      isOpen: false,
      showMobileSidebar: false,
      showSearchPopup: false,
    }
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
    isHybridRoute() {
      return this.$route.meta.isHybridRoute
    },
    showUploadTracker() {
      return this.isLoggedIn && this.$store.state.uploads.length > 0
    },
    hideInfoSideBar() {
      if (this.$route.meta.documentPage) {
        return false
      }
      if (this.$route.name === "Notifications") {
        return false
      }
      return true
    },
  },
  mounted() {
    this.addKeyboardShortcut()
    this.emitter.on("showSearchPopup", (data) => {
      this.showSearchPopup = data
    })
  },
  methods: {
    handleDefaultContext(event) {
      if (this.$route.meta.documentPage) {
        return
      } else if (
        this.$store.state.entityInfo[0]?.mime_type ===
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document" &&
        this.$route.name === "File"
      ) {
        return
      } else {
        return event.preventDefault()
      }
    },
    async currentPageEmitTrigger() {
      this.emitter.emit("fetchFolderContents")
    },
    addKeyboardShortcut() {
      window.addEventListener("keydown", (e) => {
        if (
          e.key === "k" &&
          (e.ctrlKey || e.metaKey) &&
          !e.target.classList.contains("ProseMirror")
        ) {
          this.showSearchPopup = true
          e.preventDefault()
        }
      })
    },
  },
}
</script>
