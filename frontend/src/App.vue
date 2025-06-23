<template>
  <div
    class="w-screen h-screen antialiased"
    dark
  >
    <div
      class="bg-surface-gray-7 text-ink-white text-sm text-center py-2 sm:hidden"
    >
      Drive works best on desktop.
    </div>
    <div
      v-if="isLoggedIn || $route.meta.allowGuest"
      class="flex"
    >
      <Sidebar
        v-if="isLoggedIn && !['Teams', 'Setup'].includes($route.name)"
        class="hidden sm:block"
      />
      <div
        id="dropzone"
        class="flex flex-col h-screen flex-grow overflow-hidden bg-surface-white"
      >
        <router-view
          :key="$route.fullPath"
          v-slot="{ Component }"
        >
          <component :is="Component" />
        </router-view>
      </div>

      <BottomBar
        v-if="isLoggedIn"
        class="fixed bottom-0 w-full sm:hidden"
      />
    </div>
    <router-view
      v-else
      :key="$route.fullPath"
      v-slot="{ Component }"
    >
      <component :is="Component" />
    </router-view>
  </div>
  <SearchPopup
    v-if="isLoggedIn && showSearchPopup"
    v-model="showSearchPopup"
  />
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
import UploadTracker from "@/components/UploadTracker.vue"
import { Toasts } from "@/utils/toasts.js"
import SearchPopup from "./components/SearchPopup.vue"
import BottomBar from "./components/BottomBar.vue"
import { useStore } from "vuex"
import { ref, computed } from "vue"
import { useRouter } from "vue-router"
import { onKeyDown } from "@vueuse/core"
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

// Add keyboard shortcuts
const KEY_BINDS = {
  k: () => (showSearchPopup.value = true),
  h: () => router.push({ name: "Home" }),
  i: () => router.push({ name: "Inbox" }),
  t: () => router.push({ name: "Team" }),
  f: () => router.push({ name: "Favourites" }),
  r: () => router.push({ name: "Recents" }),
  s: () => router.push({ name: "Shared" }),
  u: () => emitter.emit("uploadFile"),
  U: () => emitter.emit("uploadFolder"),
  u: () => emitter.emit("uploadFile"),
  N: () => emitter.emit("newFolder"),
  m: () => store.state.activeEntity && emitter.emit("move"),
  Enter: () => store.state.activeEntity && emitter.emit("rename"),
}
for (let k in KEY_BINDS) {
  onKeyDown(k, (e) => {
    if (e.ctrlKey) {
      KEY_BINDS[k](e)
      e.preventDefault()
    }
  })
}

onKeyDown((e) => {
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  if (e.key == "?") emitter.emit("toggleShortcuts")
  if (e.metaKey) {
    if (e.key == ",") {
      emitter.emit("showSettings")
      e.preventDefault()
    }
    if (e.shiftKey) {
      if (e.key == "ArrowRight") {
        store.commit("setIsSidebarExpanded", true)
        e.preventDefault()
      } else if (e.key == "ArrowLeft") {
        store.commit("setIsSidebarExpanded", false)
        e.preventDefault()
      }
    }
    // Support Cmd + K also
    if (e.key == "k") {
      showSearchPopup.value = true
      e.preventDefault()
    }
  }
})
</script>
