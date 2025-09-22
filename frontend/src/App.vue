<template>
  <FrappeUIProvider>
    <div
      v-if="isLoggedIn || $route.meta.allowGuest"
      class="flex flex-col sm:flex-row h-full"
    >
      <Sidebar v-if="normalView" />
      <div
        id="dropzone"
        class="flex flex-col flex-1 overflow-hidden bg-surface-white relative"
      >
        <router-view
          :key="$route.fullPath"
          v-slot="{ Component }"
        >
          <component :is="Component" />
        </router-view>
      </div>
      <BottomBar
        v-if="!inIframe && isLoggedIn"
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
    <button
      accesskey="u"
      class="hidden"
      @click="emitter.emit('uploadFile')"
    />
    <FileUploader
      v-if="normalView && ['Folder', 'Home', 'Team'].includes($route.name)"
    />
    <FDialogs />
  </FrappeUIProvider>
</template>
<script setup>
import Sidebar from "@/components/Sidebar.vue"
import SearchPopup from "./components/SearchPopup.vue"
import FDialogs from "./components/FDialogs.vue"
import BottomBar from "./components/BottomBar.vue"
import FileUploader from "@/components/FileUploader.vue"
import { useStore } from "vuex"
import { ref, computed, provide } from "vue"
import { onKeyDown } from "@vueuse/core"
import emitter from "@/emitter"
import { FrappeUIProvider } from "frappe-ui"
import { useRoute } from "vue-router"
import "access-key-label-polyfill"

const store = useStore()
const route = useRoute()
const inIframe = window.self !== window.top
provide("inIframe", inIframe)

const showSearchPopup = ref(false)
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const normalView = computed(
  () =>
    !inIframe && isLoggedIn.value && !["Teams", "Setup"].includes(route.name)
)
emitter.on("showSearchPopup", (data) => {
  showSearchPopup.value = data
})

const EMITTERS = {
  u: () => emitter.emit("uploadFile"),
  n: () => emitter.emit("newFolder"),
  m: () => emitter.emit("move"),
  p: () => emitter.emit("share"),
  e: () => emitter.emit("rename"),
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
