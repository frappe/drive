<template>
  <Dialog v-model="open" :options="{ size: 'lg' }">
    <template #body>
      <div class="pr-5 py-5">
        <div class="flex items-center justify-start w-full gap-1">
          <span class="font-semibold text-2xl pl-5">Move</span>
          <div
            class="grid grid-flow-col items-center justify-start transition-colors text-gray-800 bg-white border truncate border-gray-300 h-7 text-base pr-2 rounded max-w-[80%] overflow-hidden">
            <Folder
              class="h-4 stroke-[1.5] text-gray-900"
              v-if="
                store.state.entityInfo.length === 1 &&
                store.state.entityInfo[0].is_group
              " />
            <File class="h-4 stroke-[1.5] text-gray-900" v-else />
            <span
              class="font-medium text-base text-gray-800 line-clamp-1 truncate">
              {{ DialogTitle }}
            </span>
          </div>
          <Button
            class="ml-auto"
            variant="minimal"
            @click="$emit('update:modelValue', false)">
            <FeatherIcon name="x" class="stroke-2 ml-auto h-4" />
          </Button>
        </div>
        <Tabs
          v-model="tabIndex"
          #default="{ tab }"
          :tabs="tabs"
          class="mb-2"></Tabs>
        <div
          class="flex flex-col justify-items-start pl-3 min-h-[40vh] justify-start max-h-[40vh] overflow-y-scroll">
          <NoFilesSection
            v-if="!folderContents?.length"
            class="my-auto"
            primary-message="Nothing in here"
            secondary-message="" />
          <div
            v-for="entity in folderContents"
            :id="entity.name"
            :key="entity.name"
            class="entity grid items-center cursor-pointer mb-1 rounded pl-2 pr-4 py-1.5 hover:bg-gray-50 group hover:bg-gray-100"
            :draggable="false"
            @click="openEntity(entity)"
            @dragenter.prevent
            @dragover.prevent
            @mousedown.stop>
            <div
              class="flex items-center text-gray-800 text-sm font-medium truncate"
              :draggable="false">
              <svg
                v-if="entity.is_group"
                :style="{ fill: entity.color }"
                :draggable="false"
                class="h-[20px] mr-3"
                viewBox="0 0 30 30"
                xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z" />
              </svg>
              <img
                v-else
                :src="getIconUrl(formatMimeType(entity.mime_type))"
                :draggable="false"
                class="h-[20px] mr-3" />
              {{ entity.title }}
            </div>
          </div>
        </div>
        <div v-if="breadcrumbs.length > 1" class="pl-5 flex mt-5">
          <div v-for="(crumb, index) in breadcrumbs">
            <span
              v-if="breadcrumbs.length > 1 && index > 0"
              class="text-gray-600 mx-1">
              {{ "/" }}
            </span>
            <button
              class="text-base cursor-pointer"
              :class="
                breadcrumbs.length - 1 === index
                  ? 'text-gray-900'
                  : 'text-gray-600'
              "
              @click="closeEntity(index)">
              {{ crumb.title }}
            </button>
          </div>
        </div>
        <div class="w-full flex items-center justify-between">
          <Button
            :disabled="disableNewFolder"
            :variant="'subtle'"
            class="ml-5 mt-2"
            :loading="folderContents?.loading"
            icon-left="folder-plus">
            New Folder
          </Button>
          <Button
            variant="solid"
            @click="
              move.submit({
                entity_names: store.state.entityInfo.map((obj) => obj.name),
                new_parent: currentFolder,
              })
            "
            class="mt-2"
            :loading="move.loading">
            <template #prefix>
              <FolderInput class="w-4" />
            </template>
            Move
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import NoFilesSection from "./NoFilesSection.vue";
import { watch, defineEmits, computed, h, ref, onMounted } from "vue";
import { createResource, Dialog, FeatherIcon, Button, Tabs } from "frappe-ui";
import { formatSize, formatDate, formatMimeType } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";
import { useStore } from "vuex";
import { FolderInput, Folder, File, Turtle } from "lucide-vue-next";
import { Star, Home, Users, Plus, Upload } from "lucide-vue-next";

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
});
const store = useStore();
const tabIndex = ref(props.suggestedTabIndex);
const folderContents = ref();
const folderName = ref("");
const breadcrumbs = ref([{ name: store.state.homeFolderID, title: "Home" }]);

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
];

const isEmpty = computed(() => {
  return folderContents.value && folderContents.value.length === 0;
});

const disableNewFolder = computed(() => {
  if (tabIndex.value !== 0) {
    return true;
  } else {
    console.log(currentFolder.value);
  }
});

const currentFolder = computed(() => {
  return breadcrumbs.value[breadcrumbs.value.length - 1].name;
});

const emit = defineEmits(["update:modelValue", "success"]);
const DialogTitle = computed(() => {
  if (store.state.entityInfo.length > 1) {
    return store.state.entityInfo.length + " items";
  } else {
    return store.state.entityInfo[0].title;
  }
});

const open = computed({
  // getter
  get() {
    return this.modelValue;
  },
  // setter
  set(newValue) {
    emit("update:modelValue", newValue);
  },
});

function openEntity(value) {
  folderPermissions.fetch();
  console.log(folderPermissions.data);
  if (value.is_group) {
    breadcrumbs.value.push({ name: value.name, title: value.title });
    if (tabIndex === 2) {
      sharedFolder.fetch({
        entity_name: currentFolder.value,
      });
    } else {
      ownedFolder.fetch({
        entity_name: currentFolder.value,
        is_active: true,
      });
    }
  }
}

function closeEntity(index) {
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1);
    if (tabIndex === 3) {
      sharedFolder.fetch({
        entity_name: currentFolder.value,
      });
    } else {
      ownedFolder.fetch({
        entity_name: currentFolder.value,
        is_active: true,
      });
    }
  }
}

watch(tabIndex, (newValue, oldValue) => {
  switch (newValue) {
    case 0:
      breadcrumbs.value = [{ name: store.state.homeFolderID, title: "Home" }];
      ownedFolder.fetch({
        entity_name: store.state.homeFolderID,
        is_active: true,
      });
      break;
    case 1:
      breadcrumbs.value = [{ name: "", title: "Favourites" }];
      favourites.fetch();
      break;
    case 2:
      breadcrumbs.value = [{ name: "", title: "Shared" }];
      sharedWithMe.fetch({ entity_name: "" });
      break;
    default:
      breadcrumbs.value = [];
      folderContents.value = [];
      break;
  }
});

let sharedWithMe = createResource({
  url: "drive.api.permissions.get_shared_with_me",
  method: "GET",
  auto: props.suggestedTabIndex === 2 ? true : false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size;
      entity.file_size = entity.is_group
        ? entity.item_count + " items"
        : formatSize(entity.file_size);
      entity.modified = formatDate(entity.modified);
      entity.creation = formatDate(entity.creation);
      entity.owner = "Me";
    });
    folderContents.value = data;
  },
  onError(error) {
    console.log(error);
  },
});

let sharedFolder = createResource({
  url: "drive.api.files.list_folder_contents",
  onSuccess(data) {
    this.folderContents.error = null;
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size;
      entity.file_size = entity.is_group ? "" : formatSize(entity.file_size);
      entity.modified = formatDate(entity.modified);
      entity.creation = formatDate(entity.creation);
      entity.owner = entity.owner === this.userId ? "Me" : entity.owner;
      this.$store.commit("setCurrentViewEntites", data);
    });
  },
  auto: false,
});

let favourites = createResource({
  url: "drive.api.files.list_favourites",
  method: "GET",
  auto: props.suggestedTabIndex === 1 ? true : false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size;
      entity.file_size = entity.is_group
        ? entity.item_count + " items"
        : formatSize(entity.file_size);
      entity.modified = formatDate(entity.modified);
      entity.creation = formatDate(entity.creation);
      entity.owner = "Me";
    });
    folderContents.value = data;
  },
  onError(error) {
    console.log(error);
  },
});

let ownedFolder = createResource({
  url: "drive.api.files.list_owned_entities",
  method: "GET",
  params: {
    is_active: true,
  },
  auto: props.suggestedTabIndex === 0 ? true : false,
  onSuccess(data) {
    data.forEach((entity) => {
      entity.size_in_bytes = entity.file_size;
      entity.file_size = entity.is_group
        ? entity.item_count + " items"
        : formatSize(entity.file_size);
      entity.modified = formatDate(entity.modified);
      entity.creation = formatDate(entity.creation);
      entity.owner = "Me";
    });
    folderContents.value = data;
  },
  onError(error) {
    console.log(error);
  },
});
let move = createResource({
  url: "drive.api.files.move",
  method: "POST",
  auto: false,
  onSuccess(data) {
    emit("success", store.state.entityInfo[0].name);
  },
});

let folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value.name,
    fields: "title,is_group,allow_comments,allow_download,owner",
  },
  onSuccess(data) {
    this.entity = data;
  },
  auto: false,
});

let NewFolder = createResource({
  url: "drive.api.files.create_folder",
  params: {
    title: folderName.value,
    parent: currentFolder.value,
  },
  onSuccess(data) {
    console.log(data);
  },
  onError(error) {
    console.log(error);
  },
});
</script>
