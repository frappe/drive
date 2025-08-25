<template>
  <FrappeUIProvider>
    <div
      v-if="isLoggedIn || $route.meta.allowGuest"
      class="flex flex-col sm:flex-row h-full"
    >
      <Sidebar v-if="isLoggedIn && !['Teams', 'Setup'].includes($route.name)" />
      <div
        id="dropzone"
        class="flex flex-col flex-1 overflow-hidden bg-surface-white"
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
        class="w-full sm:hidden"
      />
    </div>
    <router-view
      v-else
      :key="$route.fullPath"
      v-slot="{ Component }"
    >
      <component :is="Component" />
    </router-view>
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
    <button
      accesskey="u"
      class="hidden"
      @click="emitter.emit('uploadFile')"
    />
  </FrappeUIProvider>
</template>
<script setup>
import Sidebar from "@/components/Sidebar.vue"
import UploadTracker from "@/components/UploadTracker.vue"
import SearchPopup from "./components/SearchPopup.vue"
import BottomBar from "./components/BottomBar.vue"
import { useStore } from "vuex"
import { ref, computed } from "vue"
import { useRouter } from "vue-router"
import { onKeyDown } from "@vueuse/core"
import emitter from "@/emitter"
import { FrappeUIProvider } from "frappe-ui"
import "access-key-label-polyfill"

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

const EMITTERS = {
  u: () => emitter.emit("uploadFile"),
  n: () => emitter.emit("newFolder"),
  m: () => store.state.activeEntity && emitter.emit("move"),
  p: () => store.state.activeEntity && emitter.emit("share"),
  e: () => store.state.activeEntity && emitter.emit("rename"),
}
for (let k in EMITTERS) {
  const btn = document.createElement("button")
  btn.style.display = "none"
  btn.accessKey = k
  btn.onclick = EMITTERS[k]
  document.body.appendChild(btn)
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
        store.commit("setSidebarCollapsed", false)
      } else if (e.key == "ArrowLeft") {
        store.commit("setSidebarCollapsed", true)
        e.preventDefault()
      }
    }
    if (e.key == "k") {
      showSearchPopup.value = true
      e.preventDefault()
    }
  }
})
</script>
