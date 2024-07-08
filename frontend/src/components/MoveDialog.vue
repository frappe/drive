<template>
  <Dialog v-model="open" :options="{ title: DialogTitle, size: 'lg' }">
    <template #body-content>
      <Tabs v-model="tabIndex" :tabs="tabs" tablist-class="pl-0 mb-2">
        <div
          v-if="folderContents?.length"
          class="flex flex-col justify-items-start h-[40vh] justify-start overflow-y-auto"
        >
          <div v-for="item in folderContents" :id="item.name" :key="item.name">
            <div
              class="px-4 grid items-center cursor-pointer rounded h-8 group hover:bg-gray-100"
              :draggable="false"
              @click="openEntity(item)"
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
            <div class="border-t w-full mx-auto max-w-[95%]"></div>
          </div>
        </div>
        <div class="flex flex-col items-center justify-center h-[40vh]" v-else>
          <Folder class="text-gray-600 h-10 w-auto" />
          <span class="text-gray-600 text-base mt-2">Folder is Empty</span>
        </div>
        <div
          class="flex items-center px-2"
          :class="breadcrumbs.length > 1 ? 'visible' : 'invisible'"
        >
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
                breadcrumbs.length - 1 === index
                  ? 'text-gray-900 text-base font-medium p-1'
                  : 'text-gray-600 text-base rounded-[6px] hover:bg-gray-100 p-1'
              "
              @click="closeEntity(crumb.name)"
            >
              {{ crumb.title }}
            </button>
          </div>
        </div>
      </Tabs>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        :loading="move.loading"
        :disabled="!evalPermission"
        @click="
          move.submit({
            entity_names: store.state.entityInfo.map((obj) => obj.name),
            new_parent: currentFolder,
          })
        "
      >
        <template #prefix>
          <Move></Move>
        </template>
        Move
      </Button>
    </template>
  </Dialog>
</template>
<script setup>
import { watch, defineEmits, computed, h, ref } from "vue"
import { createResource, Dialog, Button, Tabs, Dropdown } from "frappe-ui"
import { formatSize, formatDate, formatMimeType } from "@/utils/format"
import { useStore } from "vuex"
import Home from "./EspressoIcons/Home.vue"
import Star from "./EspressoIcons/Star.vue"
import Users from "./EspressoIcons/Users.vue"
import Move from "./EspressoIcons/Move.vue"
import Folder from "./EspressoIcons/Folder.vue"

const store = useStore()
const currentFolder = ref(store.state.homeFolderID)
const emit = defineEmits(["update:modelValue", "success"])
const props = defineProps({
  entity: {
    type: Object,
    required: false,
    default: null,
  },
})

const open = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})

const evalPermission = computed(() => {
  if (currentFolder.value) {
    if (
      folderPermissions.data?.owner === currentUserEmail.value ||
      folderPermissions.data?.write === 1
    ) {
      return true
    }
    if (currentFolder.value === store.state.homeFolderID) {
      return true
    }
  }
  return false
})

const DialogTitle = computed(() => {
  if (store.state.entityInfo.length > 1) {
    return `Moving ${store.state.entityInfo.length} items`
  } else {
    return `Moving "${store.state.entityInfo[0].title}"`
  }
})

const currentUserEmail = computed(() => {
  return store.state.auth.user_id
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
const folderContents = ref()
const breadcrumbs = ref([{ name: store.state.homeFolderID, title: "Home" }])

const folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value,
  },
  auto: false,
})

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
        file_kind_list: JSON.stringify(["Folder"]),
      })
      break
    case 1:
      breadcrumbs.value = [{ name: "", title: "Favourites" }]
      currentFolder.value = null
      fetchFolderContents.fetch({
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

function openEntity(value) {
  currentFolder.value = value.name
  folderPermissions.fetch({
    entity_name: value.name,
    fields: "title,is_group,allow_comments,allow_download,owner",
  })
  breadcrumbs.value.push({ name: value.name, title: value.title })
  fetchFolderContents.fetch({
    entity_name: currentFolder.value,
    is_active: 1,
    recents_only: false,
    favourites_only: false,
    file_kind_list: JSON.stringify(["Folder"]),
  })
}

function closeEntity(name) {
  const index = breadcrumbs.value.findIndex((obj) => obj.name === name)
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
    currentFolder.value = breadcrumbs.value[breadcrumbs.value.length - 1].name
    if (tabIndex.value === 2 && !currentFolder.value.length) {
      sharedWithMe.fetch({
        is_active: 1,
        recents_only: false,
        favourites_only: false,
        file_kind_list: JSON.stringify(["Folder"]),
      })
    } else {
      fetchFolderContents.fetch({
        entity_name: currentFolder.value,
        is_active: 1,
        recents_only: false,
        favourites_only: tabIndex.value === 1 ? true : false,
        file_kind_list: JSON.stringify(["Folder"]),
      })
    }
  }
}

const fetchFolderContents = createResource({
  method: "GET",
  url: "drive.api.list.files",
  auto: true,
  params: {
    entity_name: currentFolder.value,
    is_active: 1,
    recents_only: false,
    favourites_only: false,
    file_kind_list: JSON.stringify(["Folder"]),
  },
  onSuccess(data) {
    folderContents.value = []
    folderContents.value = data
  },
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

let sharedWithMe = createResource({
  url: "drive.api.list.shared_with_user",
  method: "GET",
  auto: false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size
      entity.file_size = entity.is_group
        ? entity.item_count + " items"
        : formatSize(entity.file_size)
      entity.modified = formatDate(entity.modified)
      entity.creation = formatDate(entity.creation)
    })
    folderContents.value = data
  },
  onError(error) {
    console.log(error)
  },
})

const move = createResource({
  url: "drive.api.files.move",
  method: "POST",
  auto: false,
  onSuccess() {
    emit(
      "success",
      store.state.entityInfo[0].name,
      store.state.entityInfo[store.state.entityInfo.length - 1].name
    )
  },
})
</script>
