<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Open a file', size: '5xl' }"
  >
    <template #body>
      <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9 px-6 pt-5">
        Open a file
      </h3>
      <div class="px-2 pt-2">
        <div class="flex items-center justify-start px-4 my-2">
          <Dropdown
            v-if="dropDownItems.length"
            :options="dropDownItems"
          >
            <button class="flex">
              <svg
                class="size-4 m-auto text-ink-gray-5"
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="1"
                />
                <circle
                  cx="19"
                  cy="12"
                  r="1"
                />
                <circle
                  cx="5"
                  cy="12"
                  r="1"
                />
              </svg>
            </button>
          </Dropdown>

          <span
            v-if="dropDownItems.length"
            class="text-ink-gray-5 mx-0.5"
          >
            {{ "/" }}
          </span>
          <div
            v-for="(crumb, index) in lastFourBreadCrumbs"
            :key="index"
          >
            <span
              v-if="breadcrumbs.length > 1 && index > 0"
              class="text-ink-gray-5 mx-0.5"
            >
              {{ "/" }}
            </span>
            <button
              class="text-base cursor-pointer"
              :class="
                breadcrumbs.length - 1 === index
                  ? 'text-ink-gray-9 text-base font-medium p-1'
                  : 'text-ink-gray-5 text-base rounded-[6px] hover:bg-surface-gray-2 p-1'
              "
              @click="closeEntity(crumb.name)"
            >
              {{ crumb.title }}
            </button>
          </div>
        </div>

        <div
          class="flex"
          :style="{ height: 'calc(100vh - 20rem)' }"
        >
          <Tabs
            v-model="tabIndex"
            :tabs="tabs"
          >
            <div
              v-if="tabIndex === 4"
              class="flex flex-col h-full items-center justify-center p-4"
            >
              <Button
                size="md"
                variant="solid"
                @click="emitter.emit('uploadFile')"
              >
                <template #prefix>
                  <Upload class="w-4 stroke-1.5" />
                </template>
                Upload
              </Button>
              <!-- <span class="text-ink-gray-7 text-base mt-2" >Or drag a file here to upload</span> -->
            </div>
            <NoFilesSection
              v-else-if="isEmpty"
              class="my-auto"
              primary-message="No Files"
              secondary-message=" "
            />
            <div
              v-else
              class="h-full p-4"
            >
              <div class="mt-2">
                <div class="flex py-1 justify-between">
                  <span
                    v-if="folders.length > 0"
                    class="text-ink-gray-5 font-medium text-base"
                  >
                    Folders
                  </span>
                  <span v-else />
                  <Button
                    v-if="folderStack.length > 1"
                    variant="ghost"
                    icon="arrow-up"
                    class="border"
                    :class="[
                      $store.state.view === 'list'
                        ? 'bg-surface-white shadow'
                        : '',
                    ]"
                    @click="closeEntity()"
                  />
                </div>
                <div class="flex flex-row flex-wrap gap-4 mt-0.5">
                  <div
                    v-for="folder in folders"
                    :id="folder.name"
                    :key="folder.name"
                    class="cursor-pointer p-2 w-40 h-26 rounded-lg border group select-none entity border-outline-gray-modals hover:shadow-2xl"
                    draggable="false"
                    @click="openEntity(folder)"
                    @dragenter.prevent
                    @dragover.prevent
                    @mousedown.stop
                  >
                    <div class="flex items-start">
                      <svg
                        :style="{ fill: folder.color }"
                        :draggable="false"
                        class="h-6 w-auto"
                        viewBox="0 0 30 30"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z"
                        />
                      </svg>
                    </div>
                    <div class="content-center grid">
                      <span class="truncate text-sm text-ink-gray-8 mt-2">
                        {{ folder.title }}
                      </span>
                      <p class="truncate text-xs text-ink-gray-5 mt-0">
                        {{ folder.file_size }}
                        {{ !!folder.file_size ? "∙" : null }}
                        {{ folder.relativeModified }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-if="files.length > 0"
                :class="folders.length > 0 ? 'mt-8' : 'mt-2'"
              >
                <div class="text-ink-gray-5 font-medium text-base">Files</div>
                <div class="inline-flex flex-row flex-wrap gap-4 mt-0.5">
                  <div
                    v-for="file in files"
                    :id="file.name"
                    :key="file.name"
                    class="w-40 h-40 rounded-lg border group select-none entity cursor-pointer relative group border-outline-gray-modals hover:shadow-2xl"
                    :draggable="false"
                    @click="openEntity(file)"
                    @dragenter.prevent
                    @dragover.prevent
                    @mousedown.stop
                  >
                    <GridItem
                      :file_kind="file.file_kind"
                      :mime_type="file.mime_type"
                      :file_ext="file.file_ext"
                      :name="file.name"
                      :title="file.title"
                      :modified="file.modified"
                      :relative-modified="file.relativeModified"
                      :file_size="file.file_size"
                    />
                  </div>
                </div>
              </div>
            </div>
          </Tabs>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import NoFilesSection from "./NoFilesSection.vue"
import GridItem from "./GridItem.vue"
import { watch, defineEmits, computed, h, ref } from "vue"
import { useTimeAgo } from "@vueuse/core"
import { createResource, Dialog, Button, Tabs, Dropdown } from "frappe-ui"
import LucideClock from "~icons/lucide/clock"
import LucideHome from "~icons/lucide/home"
import LucidePlus from "~icons/lucide/plus"
import LucideStar from "~icons/lucide/star"
import LucideUsers from "~icons/lucide/users"
import Upload from "~icons/lucide/upload"

import { formatSize, formatDate } from "@/utils/format"
import { useStore } from "vuex"

const props = defineProps({
  title: {
    type: String,
    default: "Open a File",
  },
  suggestedTabIndex: {
    type: Number,
    default: 0,
  },
})

const store = useStore()
const currentFolder = ref(store.state.homeFolderID)
const emit = defineEmits(["update:modelValue", "success"])
const tabIndex = ref(props.suggestedTabIndex)
const folderContents = ref()
const folderStack = ref([""])
const breadcrumbs = ref([{ name: store.state.homeFolderID, title: "Home" }])

const isEmpty = computed(() => {
  return folderContents.value && folderContents.value.length === 0
})
const folders = computed(() => {
  return folderContents.value
    ? folderContents.value.filter((x) => x.is_group === 1)
    : []
})

const files = computed(() => {
  return folderContents.value
    ? folderContents.value.filter((x) => x.is_group === 0)
    : []
})

const open = computed({
  // getter
  get() {
    return props.modelValue
  },
  // setter
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})

const tabs = [
  {
    label: "Home",
    icon: h(LucideHome, { class: "size-4" }),
    component: NoFilesSection,
  },
  {
    label: "Recents",
    icon: h(LucideClock, { class: "size-4" }),
  },
  {
    label: "Favourite",
    icon: h(LucideStar, { class: "size-4" }),
  },
  {
    label: "Shared",
    icon: h(LucideUsers, { class: "size-4" }),
  },
  {
    label: "Upload",
    icon: h(LucidePlus, { class: "size-4 stroke-[1.5]" }),
  },
]

watch(tabIndex, (newValue) => {
  switch (newValue) {
    case 0:
      breadcrumbs.value = [{ name: store.state.homeFolderID, title: "Home" }]
      currentFolder.value = store.state.homeFolderID
      fetchFolderContents.fetch({
        entity_name: currentFolder.value,
        is_active: 1,
        recents_only: false,
        favourites_only: false,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
      break
    case 1:
      breadcrumbs.value = [{ name: "", title: "Recents" }]
      currentFolder.value = null
      fetchFolderContents.fetch({
        entity_name: "",
        is_active: 1,
        recents_only: true,
        favourites_only: false,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
      break
    case 2:
      breadcrumbs.value = [{ name: "", title: "Favourites" }]
      currentFolder.value = null
      fetchFolderContents.fetch({
        is_active: 1,
        recents_only: false,
        favourites_only: true,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
      break
    case 3:
      breadcrumbs.value = [{ name: "", title: "Shared" }]
      currentFolder.value = null
      sharedWithMe.fetch({
        is_active: 1,
        recents_only: false,
        favourites_only: true,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
      break
    default:
      breadcrumbs.value = []
      folderContents.value = []
      break
  }
})

const lastFourBreadCrumbs = computed(() => {
  if (breadcrumbs.value.length > 4) {
    return breadcrumbs.value.slice(-4)
  }
  return breadcrumbs.value
})

const dropDownItems = computed(() => {
  let allExceptLastTwo = breadcrumbs.value.slice(0, -4)
  return allExceptLastTwo.map((item) => {
    return {
      ...item,
      icon: null,
      label: item.title,
      onClick: () => closeEntity(item.name),
    }
  })
})

function openEntity(value) {
  if (value.is_group) {
    currentFolder.value = value.name
    folderPermissions.fetch({
      entity_name: value.name,
      fields: "title,is_group,allow_download,owner",
    })
    breadcrumbs.value.push({ name: value.name, title: value.title })
    fetchFolderContents.fetch({
      entity_name: currentFolder.value,
      is_active: 1,
      recents_only: false,
      favourites_only: false,
      mime_type_list: JSON.stringify([
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ]),
    })
  } else {
    emit("success", value)
  }
}

function closeEntity(name) {
  const index = breadcrumbs.value.findIndex((obj) => obj.name === name)
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
    currentFolder.value = breadcrumbs.value[breadcrumbs.value.length - 1].name
    if (tabIndex.value === 3 && !currentFolder.value.length) {
      sharedWithMe.fetch({
        is_active: 1,
        recents_only: false,
        favourites_only: false,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
    } else {
      fetchFolderContents.fetch({
        entity_name: currentFolder.value,
        is_active: 1,
        recents_only: false,
        favourites_only: tabIndex.value === 1 ? true : false,
        mime_type_list: JSON.stringify([
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]),
      })
    }
  }
}

const folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value,
  },
  auto: false,
})

const fetchFolderContents = createResource({
  method: "GET",
  url: "drive.api.list.files",
  auto: true,
  params: {
    entity_name: currentFolder.value,
    is_active: 1,
    recents_only: false,
    favourites_only: false,
    mime_type_list: JSON.stringify([
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]),
  },
  onSuccess(data) {
    folderContents.value = []
    data.forEach((entity) => {
      entity.file_size = entity.is_group ? null : formatSize(entity.file_size)
      entity.relativeModified = useTimeAgo(entity.modified)
      entity.modified = formatDate(entity.modified)
      entity.creation = formatDate(entity.creation)
    })
    folderContents.value = data
  },
  // Better error handling
})

let sharedWithMe = createResource({
  url: "drive.api.list.shared_with_user",
  method: "GET",
  auto: false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.file_size = entity.is_group ? null : formatSize(entity.file_size)
      entity.relativeModified = useTimeAgo(entity.modified)
      entity.modified = formatDate(entity.modified)
      entity.creation = formatDate(entity.creation)
    })
    folderContents.value = data
  },
})
</script>
