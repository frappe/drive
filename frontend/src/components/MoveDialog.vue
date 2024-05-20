<template>
  <Dialog v-model="open" :options="{ title: DialogTitle, size: 'md' }">
    <template #body>
      <div class="p-5">
        <div class="flex items-start w-full justify-between gap-x-15 mb-5">
          <span class="font-semibold text-2xl truncate">{{ DialogTitle }}</span>
          <Button
            class="ml-auto"
            variant="ghost"
            @click="$emit('update:modelValue', false)"
          >
            <FeatherIcon name="x" class="stroke-2 h-4" />
          </Button>
        </div>

        <Tabs v-model="tabIndex" :tabs="tabs" tablist-class="pl-0 mb-4"></Tabs>

        <div
          class="flex flex-col justify-items-start min-h-[40vh] justify-start max-h-[40vh] overflow-y-scroll pb-5"
        >
          <NoFilesSection
            v-if="!folderContents?.length"
            class="my-auto"
            primary-message="Nothing in here"
            secondary-message=""
          />
          <div
            v-for="entity in folderContents"
            :id="entity.name"
            :key="entity.name"
          >
            <div
              class="entity grid items-center cursor-pointer rounded pl-2 pr-4 py-1.5 group hover:bg-gray-100"
              :draggable="false"
              @click="openEntity(entity)"
              @dragenter.prevent
              @dragover.prevent
              @mousedown.stop
            >
              <div
                class="flex items-center text-gray-800 text-sm font-medium truncate"
                :draggable="false"
              >
                <svg
                  v-if="entity.is_group"
                  :style="{ fill: entity.color }"
                  :draggable="false"
                  class="h-[20px] mr-3"
                  viewBox="0 0 30 30"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z"
                  />
                </svg>
                <img
                  v-else
                  :src="getIconUrl(formatMimeType(entity.mime_type))"
                  :draggable="false"
                  class="h-[20px] mr-3"
                />
                {{ entity.title }}
              </div>
            </div>
            <div class="border-t w-full mx-auto max-w-[95%]"></div>
          </div>
        </div>
        <div class="flex text-sm mt-2 mb-6 px-2">
          <div v-for="(crumb, index) in breadcrumbs" :key="index">
            <span
              v-if="breadcrumbs.length > 1 && index > 0"
              class="text-gray-600 mx-1"
            >
              {{ ">" }}
            </span>
            <button
              class="text-base cursor-pointer"
              :class="
                breadcrumbs.length - 1 === index
                  ? 'text-gray-900'
                  : 'text-gray-600'
              "
              @click="closeEntity(index)"
            >
              {{ crumb.title }}
            </button>
          </div>
        </div>
        <div class="w-full flex items-center justify-between mt-2">
          <!-- <Button
          :disabled="disableNewFolder"
          :variant="'subtle'"
          :loading="folderContents?.loading"
        >
          <template #prefix><NewFolder /></template>
          New Folder
        </Button> -->
          <Button
            variant="solid"
            class="mt-2 w-full"
            :loading="move.loading"
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
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import NoFilesSection from "./NoFilesSection.vue"
import { watch, defineEmits, computed, h, ref } from "vue"
import { createResource, Dialog, FeatherIcon, Button, Tabs } from "frappe-ui"
import { formatSize, formatDate, formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import Home from "./EspressoIcons/Home.vue"
import Star from "./EspressoIcons/Star.vue"
import Users from "./EspressoIcons/Users.vue"
import Move from "./EspressoIcons/Move.vue"
import NewFolder from "./EspressoIcons/NewFolder.vue"

const props = defineProps({
  entity: {
    type: Object,
    required: false,
    default: null,
  },
  suggestedTabIndex: {
    type: Number,
    default: 0,
  },
})
const store = useStore()
const tabIndex = ref(props.suggestedTabIndex)
const folderContents = ref()
const folderName = ref("")
const breadcrumbs = ref([{ name: store.state.homeFolderID, title: "Home" }])

const tabs = [
  {
    label: "Home",
    icon: h(Home, { class: "w-4 h-4" }),
    component: NoFilesSection,
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

const disableNewFolder = computed(() => {
  if (tabIndex.value === 0 && !!currentFolder.value) {
    return false
  }
  if (folderPermissions.data?.owner === currentUserEmail.value) {
    return false
  } else if (folderPermissions.data?.write) {
    return false
  }
  return true
})

const currentUserEmail = computed(() => {
  return store.state.auth.user_id
})

const currentFolder = computed(() => {
  if (breadcrumbs.value.length) {
    return breadcrumbs.value[breadcrumbs.value.length - 1].name
  }
  return store.state.homeFolderID
})

const emit = defineEmits(["update:modelValue", "success"])
const DialogTitle = computed(() => {
  if (store.state.entityInfo.length > 1) {
    return `Moving ${store.state.entityInfo.length} items`
  } else {
    return `Moving "${store.state.entityInfo[0].title}"`
  }
})

const open = computed({
  // getter
  get() {
    return this.modelValue
  },
  // setter
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})

function openEntity(value) {
  folderPermissions.fetch({
    entity_name: value.name,
    fields: "title,is_group,allow_comments,allow_download,owner",
  })
  if (value.is_group) {
    breadcrumbs.value.push({ name: value.name, title: value.title })
    fetchFolderContents.fetch({
      entity_name: currentFolder.value,
      is_active: 1,
      recents_only: false,
      favourites_only: false,
      file_kind_list: JSON.stringify(["Folder"]),
    })
  }
}

function closeEntity(index) {
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
    if (tabIndex.value === 1) {
      favourites.fetch()
    } else {
      fetchFolderContents.fetch({
        entity_name: currentFolder.value,
        is_active: 1,
        recents_only: false,
        favourites_only: false,
        file_kind_list: JSON.stringify(["Folder"]),
      })
    }
  }
}

watch(tabIndex, (newValue) => {
  switch (newValue) {
    case 0:
      breadcrumbs.value = [{ name: store.state.homeFolderID, title: "Home" }]
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
      favourites.fetch()
      break
    case 2:
      breadcrumbs.value = [{ name: "", title: "Shared" }]
      sharedWithMe.fetch({
        entity_name: "",
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

let sharedWithMe = createResource({
  url: "drive.api.list.shared_with_user",
  method: "GET",
  auto: props.suggestedTabIndex === 2 ? true : false,
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

let fetchFolderContents = createResource({
  method: "GET",
  url: "drive.api.list.files",
  auto: props.suggestedTabIndex === 0 ? true : false,
  params: {
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

let favourites = createResource({
  url: "drive.api.list.files",
  params: {
    is_active: 1,
    recents_only: false,
    favourites_only: true,
    file_kind_list: JSON.stringify(["Folder"]),
  },
  method: "GET",
  auto: props.suggestedTabIndex === 1 ? true : false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size
      entity.file_size = entity.is_group
        ? entity.item_count + " items"
        : formatSize(entity.file_size)
      entity.modified = formatDate(entity.modified)
      entity.creation = formatDate(entity.creation)
      entity.owner = "You"
    })
    folderContents.value = data
  },
  onError(error) {
    console.log(error)
  },
})

let move = createResource({
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

let folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value,
  },
  onSuccess(data) {
    console.log(data)
  },
  auto: false,
})

let CreateNewFolder = createResource({
  url: "drive.api.files.create_folder",
  params: {
    title: folderName.value,
    parent: currentFolder.value,
  },
  onSuccess(data) {
    console.log(data)
  },
  onError(error) {
    console.log(error)
  },
})
</script>
