<template>
  <Dialog v-model="open" :options="{ title: DialogTitle, size: '2xl' }">
    <template #body-content>
      <Autocomplete
        v-if="fetchAllFolders.data"
        v-model="folderSearch"
        placeholder="Go to..."
        :options="
          fetchAllFolders.data.filter((k) =>
            currentFolder === ''
              ? k.label !== 'Home'
              : k.value !== currentFolder
          )
        "
      ></Autocomplete>
      <Tabs v-model="tabIndex" :tabs="tabs" tablist-class="!pl-0">
        <div
          v-if="folderContents.data?.length"
          class="flex flex-col justify-items-start h-[45vh] overflow-y-auto justify-start my-2"
        >
          <div
            v-for="(item, index) in folderContents.data"
            :id="item.name"
            :key="item.name"
            class=""
          >
            <div
              v-show="index > 0"
              class="border-t w-full mx-auto max-w-[96%]"
            ></div>
            <div
              class="px-3 grid items-center rounded h-9 group select-none"
              :class="
                !item.write
                  ? 'cursor-not-allowed opacity-75'
                  : 'cursor-pointer hover:bg-gray-100'
              "
              :draggable="false"
              @click="item.write ? openEntity(item) : null"
              @dragenter.prevent
              @dragover.prevent
              @mousedown.stop
            >
              <div
                class="flex items-center text-gray-800 text-base font-medium truncate"
                :draggable="false"
              >
                <svg
                  v-if="item.is_group"
                  :style="{ fill: item.color }"
                  :draggable="false"
                  class="h-4.5 mr-2"
                  viewBox="0 0 30 30"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z"
                  />
                </svg>
                <img
                  v-else
                  :src="getIconUrl(formatMimeType(item.mime_type))"
                  :draggable="false"
                  class="h-[20px] mr-3"
                />
                {{ item.title }}
              </div>
            </div>
          </div>
        </div>
        <div
          v-else
          class="flex flex-col items-center justify-center h-[45vh] my-2"
        >
          <Folder class="text-gray-600 h-10 w-auto" />
          <span class="text-gray-600 text-base mt-2">Folder is Empty</span>
        </div>
      </Tabs>
      <div class="flex items-center justify-between max-h-7">
        <div class="flex items-center my-2 justify-start">
          <Dropdown
            v-if="dropDownItems.length"
            class="h-7"
            :options="dropDownItems"
          >
            <Button variant="ghost">
              <template #icon>
                <svg
                  class="w-4 text-gray-600"
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
                  <circle cx="12" cy="12" r="1" />
                  <circle cx="19" cy="12" r="1" />
                  <circle cx="5" cy="12" r="1" />
                </svg>
              </template>
            </Button>
          </Dropdown>
          <span v-if="dropDownItems.length" class="text-gray-600 mx-0.5">
            {{ "/" }}
          </span>
          <div v-for="(crumb, index) in lastTwoBreadCrumbs" :key="index">
            <span
              v-if="breadcrumbs.length > 1 && index > 0"
              class="text-gray-600 mx-0.5"
            >
              {{ "/" }}
            </span>
            <button
              class="text-base cursor-pointer"
              :class="
                index === lastTwoBreadCrumbs.length - 1
                  ? 'text-gray-900 text-base font-medium p-1'
                  : 'text-gray-600 text-base rounded-[6px] hover:bg-gray-100 p-1'
              "
              @click="closeEntity(crumb.name)"
            >
              {{ crumb.title }}
            </button>
          </div>
        </div>
        <Button
          variant="solid"
          class="ml-auto"
          :loading="move.loading"
          @click="
            move.submit({
              entity_names: entities.map((obj) => obj.name),
              new_parent: currentFolder,
            })
          "
        >
          <template #prefix>
            <Move />
          </template>
          Move
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { watch, defineEmits, computed, h, ref } from "vue"
import {
  createResource,
  Dialog,
  Button,
  Tabs,
  Dropdown,
  Autocomplete,
} from "frappe-ui"
import { formatMimeType } from "@/utils/format"
import { useStore } from "vuex"
import Home from "./EspressoIcons/Home.vue"
import Star from "./EspressoIcons/Star.vue"
import Users from "./EspressoIcons/Users.vue"
import Move from "./EspressoIcons/Move.vue"
import Folder from "./EspressoIcons/Folder.vue"
import { useRoute } from "vue-router"

const route = useRoute()
const currentFolder = ref("")
const emit = defineEmits(["update:modelValue", "success"])
const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  entities: {
    type: Object,
    required: false,
    default: null,
  },
})

const open = computed({
  get() {
    return props.modelValue === "m"
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})

const DialogTitle = computed(() => {
  if (props.entities.length > 1) {
    return `Moving ${props.entities.length} items`
  } else {
    return `Moving "${props.entities[0].title}"`
  }
})

const lastTwoBreadCrumbs = computed(() => {
  if (breadcrumbs.value.length > 2) {
    return breadcrumbs.value.slice(-2)
  }
  return breadcrumbs.value
})

const dropDownItems = computed(() => {
  let allExceptLastTwo = breadcrumbs.value.slice(0, -2)
  return allExceptLastTwo.map((item) => {
    return {
      ...item,
      icon: null,
      label: item.title,
      onClick: () => closeEntity(item.name),
    }
  })
})

const tabs = [
  {
    label: "Home",
    icon: h(Home, { class: "w-4 h-4" }),
  },
  {
    label: "Favourites",
    icon: h(Star, { class: "w-4 h-4" }),
  },
  {
    label: "Shared",
    icon: h(Users, { class: "w-4 h-4" }),
  },
]

const tabIndex = ref(0)
const breadcrumbs = ref([{ name: "", title: "Home" }])
const folderSearch = ref({})

const folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value,
  },
})

watch(tabIndex, (newValue) => {
  switch (newValue) {
    case 0:
      breadcrumbs.value = [{ name: "", title: "Home" }]
      currentFolder.value = ""
      folderContents.fetch({
        entity_name: currentFolder.value,
        is_folder: 1,
      })
      break
    case 1:
      breadcrumbs.value = [{ name: "", title: "Favourites" }]
      currentFolder.value = null
      folderContents.fetch({
        entity_name: "",
        is_active: 1,
        recents_only: false,
        favourites_only: true,
        file_kind_list: JSON.stringify(["Folder"]),
      })
      break
    case 2:
      breadcrumbs.value = [{ name: "", title: "Shared" }]
      currentFolder.value = null
      sharedWithMe.fetch({
        is_active: 1,
        recents_only: false,
        favourites_only: false,
        file_kind_list: JSON.stringify(["Folder"]),
      })
      break
    default:
      breadcrumbs.value = []
      folderContents.value = []
      break
  }
})
watch(folderSearch, openEntity)

function openEntity(value) {
  currentFolder.value = value.name || value.value
  folderPermissions.fetch({
    entity_name: currentFolder.value,
  })
  breadcrumbs.value.push({
    name: value.name || value.value,
    title: value.title || value.label,
  })
  folderContents.fetch({
    entity_name: currentFolder.value,
  })
}

function closeEntity(name) {
  const index = breadcrumbs.value.findIndex((obj) => obj.name === name)
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
    currentFolder.value = breadcrumbs.value[breadcrumbs.value.length - 1].name
    folderContents.fetch({ entity_name: currentFolder.value })
  }
}

const folderContents = createResource({
  method: "GET",
  url: "drive.api.list.files",
  auto: true,
  makeParams: (params) => ({
    team: route.params.team,
    is_active: 1,
    folders: 1,
    ...params,
  }),
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      this.$store.commit("setError", {
        primaryMessage: "Forbidden",
        secondaryMessage: "Insufficient permissions for this resource",
      })
      this.$router.replace({ name: "Error" })
    }
  },
})

const fetchAllFolders = createResource({
  method: "GET",
  url: "drive.api.list.files",
  cache: "all-folders",
  auto: true,
  params: {
    team: route.params.team,
    is_active: 1,
    folders: 1,
    all: 1,
  },
  transform: (d) =>
    d.map((k) => ({
      value: k.name,
      label: k.title,
    })),
})

const move = createResource({
  url: "drive.api.files.move",
  onSuccess() {
    emit("success", currentFolder.value)
  },
})
</script>
