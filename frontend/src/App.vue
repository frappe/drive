<template>
  <template v-if="$route.meta.errorPage">
    <router-view :key="$route.fullPath" v-slot="{ Component }">
      <component :is="Component" id="currentPage" ref="currentPage" />
    </router-view>
  </template>

  <template v-else>
    <!-- Main container no scroll -->
    <div class="flex w-screen h-screen antialiased overflow-hidden">
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
          <div id="dropTarget" class="h-full w-full overflow-hidden">
            <Navbar
              v-if="$route.name == 'File' || $route.name == 'Document'"
              :mobile-sidebar-is-open="showMobileSidebar"
              @toggle-mobile-sidebar="showMobileSidebar = !showMobileSidebar"
            />
            <div class="flex w-full h-full overflow-hidden">
              <!-- Find a better way to handle the height overflow here (52px is the Navbar) -->
              <!-- what on mars is he talking about? -->
              <div
                class="flex w-full overflow-hidden"
                :class="
                  $route.name == 'File' || $route.name == 'Document'
                    ? 'h-[calc(100dvh-105px)] sm:h-[calc(100dvh-52px)]'
                    : 'h-full sm:h-full'
                "
              >
                <router-view :key="$route.fullPath" v-slot="{ Component }">
                  <component
                    :is="Component"
                    id="currentPage"
                    ref="currentPage"
                  />
                </router-view>
              </div>
              <InfoSidebar v-if="hideInfoSideBar" />
            </div>
          </div>
          <BottomBar
            v-if="isLoggedIn"
            class="fixed bottom-0 w-full sm:hidden"
          />
        </div>
        <router-view v-else />
      </div>
    </div>
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
  async mounted() {
    this.addKeyboardShortcuts()
    this.emitter.on("showSearchPopup", (data) => {
      this.showSearchPopup = data
    })
    if (!this.isLoggedIn) return
  },
  methods: {
    async currentPageEmitTrigger() {
      this.emitter.emit("fetchFolderContents")
    },
    addKeyboardShortcuts() {
      let tapped

      window.addEventListener("keydown", (e) => {
        let params = { team: localStorage.getItem("recentTeam") }
        const DOUBLE_KEY_MAPS = {
          k: () => setTimeout(() => (this.showSearchPopup = true), 15), // band aid fix as k was showing up in search
          h: () => this.$router.push({ name: "Home", params }),
          n: () => this.$router.push({ name: "Notifications", params }),
          t: () => this.$router.push({ name: "Team", params }),
          f: () => this.$router.push({ name: "Favourites", params }),
          r: () => this.$router.push({ name: "Recents", params }),
          s: () => this.$router.push({ name: "Shared" }),
        }

        const KEY_MAPS = [
          [
            (e) => e.metaKey && e.shiftKey && e.key == "ArrowRight",
            () => this.$store.commit("setIsSidebarExpanded", true),
          ],
          [
            (e) => e.metaKey && e.shiftKey && e.key == "ArrowLeft",
            () => this.$store.commit("setIsSidebarExpanded", false),
          ],
          [
            (e) => e.metaKey && e.key == "k",
            () => (this.showSearchPopup = true),
          ],
        ]

        if (
          e.target.classList.contains("ProseMirror") ||
          e.target.tagName === "INPUT"
        )
          return

        for (const key in DOUBLE_KEY_MAPS) {
          if (e.key === key) {
            if (tapped === key) {
              DOUBLE_KEY_MAPS[key]()
              tapped = null
            } else {
              tapped = key
              setTimeout(() => (tapped = null), 500)
            }
          }
        }
        for (let [keys, action] of KEY_MAPS) {
          if (keys(e)) {
            action()
            document.activeElement.blur()
          }
        }
      })
    },
  },
}
</script>
