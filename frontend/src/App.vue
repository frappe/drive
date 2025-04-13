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
      <div
        v-if="
          !isLoggedIn && ['File', 'Folder', 'Document'].includes($route.name)
        "
        class="absolute flex gap-2 bottom-4 right-4 bg-white opacity-90 shadow-md text-gray-800 px-2 py-2 rounded-sm text-sm"
      >
        <FrappeDriveLogo class="w-8 h-8 rounded my-auto" />
        <div>
          Powered by
          <span class="font-bold my-auto">Frappe Drive</span>
          <br />
          <Button
            variant="outline"
            size="sm"
            class="mt-2"
            @click="$router.push({ name: 'Signup' })"
          >
            Join now
          </Button>
        </div>
      </div>
      <div class="h-full w-full flex flex-col">
        <div class="bg-black text-white text-sm text-center py-2 sm:hidden">
          Drive works best on desktop.
        </div>
        <SearchPopup
          v-if="isLoggedIn && showSearchPopup"
          v-model="showSearchPopup"
        />
        <div
          v-if="isLoggedIn || $route.meta.allowGuest"
          class="flex flex-col h-full overflow-hidden sm:flex-row"
        >
          <Sidebar
            v-if="isLoggedIn && !['Teams', 'Setup'].includes($route.name)"
            class="hidden sm:block"
          />
          <div id="dropTarget" class="h-full w-full overflow-hidden">
            <Navbar v-if="$route.name == 'File' || $route.name == 'Document'" />
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
        <router-view v-else :key="$route.fullPath" v-slot="{ Component }">
          <component :is="Component" id="currentPage" ref="currentPage" />
        </router-view>
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
<script setup>
import Navbar from "@/components/Navbar.vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"
import Sidebar from "@/components/Sidebar.vue"
import InfoSidebar from "@/components/InfoSidebar.vue"
import UploadTracker from "@/components/UploadTracker.vue"
import { Link } from "frappe-ui"
import { Toasts } from "@/utils/toasts.js"
import SearchPopup from "./components/SearchPopup.vue"
import BottomBar from "./components/BottomBar.vue"
import { useStore } from "vuex"
import { onMounted, ref, computed } from "vue"
import { useRoute } from "vue-router"
import emitter from "@/emitter"
import { LucideArrowUpRightFromSquare } from "lucide-vue-next"
const store = useStore()
const route = useRoute()

const showSearchPopup = ref(false)
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const showUploadTracker = computed(
  () => isLoggedIn.value && store.state.uploads.length > 0
)
const hideInfoSideBar = computed(() => {
  if (route.meta.documentPage) {
    return false
  }
  if (route.name === "Inbox") {
    return false
  }
  return true
})

onMounted(() => {
  addKeyboardShortcuts()
  emitter.on("showSearchPopup", (data) => {
    showSearchPopup.value = data
  })
  if (!isLoggedIn.value) return
})

function addKeyboardShortcuts() {
  let tapped
  window.addEventListener("keydown", (e) => {
    let params = { team: localStorage.getItem("recentTeam") }
    const DOUBLE_KEY_MAPS = {
      k: () => setTimeout(() => (this.showSearchPopup = true), 15), // band aid fix as k was showing up in search
      h: () => router.push({ name: "Home", params }),
      n: () => router.push({ name: "Inbox", params }),
      t: () => router.push({ name: "Team", params }),
      f: () => router.push({ name: "Favourites", params }),
      r: () => router.push({ name: "Recents", params }),
      s: () => router.push({ name: "Shared" }),
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
      [(e) => e.metaKey && e.key == "k", () => (this.showSearchPopup = true)],
    ]
    if (
      e.target.classList.contains("ProseMirror") ||
      e.target.tagName === "INPUT" ||
      e.target.tagName === "TEXTAREA"
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
}
</script>
