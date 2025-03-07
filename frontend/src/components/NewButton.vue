<template>
  <div
    class="flex justify-center items-center absolute right-7 bottom-7"
    v-on-outside-click="() => (expanded = false)"
  >
    <transition name="fade">
      <label
        v-if="!expanded"
        @click="expanded = !expanded"
        for="file-upload"
        class="w-14 h-14 flex items-center justify-center rounded-full bg-gray-800 hover:bg-black text-white cursor-pointer shadow-lg transition-all"
      >
        <FeatherIcon
          :name="expanded ? 'minus' : 'plus'"
          class="size-7 text-white-600"
        />
      </label>
    </transition>
    <transition name="fade">
      <div
        v-if="expanded"
        class="absolute right-0 bottom-0 flex flex-col bg-black text-white text-base !text-left shadow-lg rounded-md p-1 space-y-1 w-40"
      >
        <button
          v-for="item in defaultActionItems"
          class="px-1.5 py-1 text-left hover:bg-gray-700 rounded-sm flex"
          @click="
            () => {
              item.handler()
              expanded = false
            }
          "
        >
          <component
            class="mr-2 h-4 w-4 flex-shrink-0 text-ink-white"
            :is="item.icon"
          />
          {{ item.label }}
        </button>
        <div
          class="rounded w-10 ml-auto hover:bg-gray-700"
          @click="expanded = false"
        >
          <FeatherIcon name="minus" class="mx-auto size-5 text-white" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { ref } from "vue"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import NewFile from "./EspressoIcons/NewFile.vue"
import emitter from "@/emitter"
import { createDocument } from "@/resources/files"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"

const route = useRoute()
const router = useRouter()
const store = useStore()

const newDocument = async () => {
  let data = await createDocument.submit({
    title: "Untitled Document",
    team: route.params.team,
    personal: route.name === "Home" ? 1 : 0,
    content: null,
    parent: store.state.currentFolderID,
  })
  window.open(
    router.resolve({
      name: "Document",
      params: { team: route.params.team, entityName: data.name },
    }).href
  )
}

const expanded = ref(false)
const defaultActionItems = [
  {
    label: "Upload File",
    icon: FileUpload,
    handler: () => emitter.emit("uploadFile"),
  },
  {
    label: "Upload Folder",
    icon: FolderUpload,
    handler: () => emitter.emit("uploadFolder"),
  },
  {
    label: "New Folder",
    icon: NewFolder,
    handler: () => emitter.emit("newFolder"),
  },
  {
    label: "New Document",
    icon: NewFile,
    handler: newDocument,
  },
]
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease-in-out;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
