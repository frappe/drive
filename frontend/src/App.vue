<template>
  <div class="w-screen h-screen antialiased">
    <div class="bg-black text-white text-sm text-center py-2 sm:hidden">
      Drive works best on desktop.
    </div>
    <div v-if="isLoggedIn || $route.meta.allowGuest" class="flex">
      <Sidebar
        v-if="isLoggedIn && !['Teams', 'Setup'].includes($route.name)"
        class="hidden sm:block"
      />
      <div
        id="dropzone"
        class="flex flex-col h-screen flex-grow overflow-hidden"
      >
        <router-view :key="$route.fullPath" v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </div>

      <BottomBar v-if="isLoggedIn" class="fixed bottom-0 w-full sm:hidden" />
    </div>
    <router-view v-else :key="$route.fullPath" v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </div>
  <SearchPopup v-if="isLoggedIn && showSearchPopup" v-model="showSearchPopup" />
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
<script setup>
import Sidebar from "@/components/Sidebar.vue"
import InfoSidebar from "@/components/InfoSidebar.vue"
import UploadTracker from "@/components/UploadTracker.vue"
import { Toasts } from "@/utils/toasts.js"
import SearchPopup from "./components/SearchPopup.vue"
import BottomBar from "./components/BottomBar.vue"
import { useStore } from "vuex"
import { onMounted, ref, computed } from "vue"
import { useRouter, useRoute } from "vue-router"
import emitter from "@/emitter"

const store = useStore()
const router = useRouter()

const showSearchPopup = ref(false)
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const showUploadTracker = computed(
  () => isLoggedIn.value && store.state.uploads.length > 0
)
emitter.on("showSearchPopup", (data) => {
  showSearchPopup.value = data
})

function addKeyboardShortcuts() {
  let tapped
  window.addEventListener("keydown", (e) => {
    let params = { team: localStorage.getItem("recentTeam") }
    const DOUBLE_KEY_MAPS = {
      k: () => setTimeout(() => (showSearchPopup.value = true), 15), // band aid fix as k was showing up in search
      h: () => router.push({ name: "Home", params }),
      n: () => router.push({ name: "Inbox", params }),
      t: () => router.push({ name: "Team", params }),
      f: () => router.push({ name: "Favourites", params }),
      r: () => router.push({ name: "Recents", params }),
      s: () => router.push({ name: "Shared" }),
    }

    // TODO: keyboard shortcuts
    const KEY_MAPS = [
      [
        (e) => e.metaKey && e.shiftKey && e.key == "ArrowRight",
        () => store.commit("setIsSidebarExpanded", true),
      ],
      [
        (e) => e.metaKey && e.shiftKey && e.key == "ArrowLeft",
        () => store.commit("setIsSidebarExpanded", false),
      ],
      [(e) => e.metaKey && e.key == "k", () => (showSearchPopup.value = true)],
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
onMounted(addKeyboardShortcuts)
</script>
