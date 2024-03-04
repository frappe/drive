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
          <Button
            v-if="folderStack.length > 1"
            variant="ghost"
            icon="arrow-up"
            class="border"
            @click="closeEntity()" />
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
        <div class="w-full flex items-center justify-between">
          <Button
            :variant="'subtle'"
            class="ml-5 mt-8"
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
            class="mt-8"
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

const tabIndex = ref(props.suggestedTabIndex);
const folderContents = ref();
const folderStack = ref([""]);

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

const currentFolder = computed(() => {
  return folderStack.value[folderStack.value.length - 1];
});

const emit = defineEmits(["update:modelValue", "success"]);
const store = useStore();
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
  if (value.is_group) {
    folderStack.value.push(value.name);
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

function closeEntity() {
  folderStack.value.pop();
  folderStack.value.length ? null : folderStack.value.push("");
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

watch(tabIndex, (newValue, oldValue) => {
  folderStack.value = [""];
  switch (newValue) {
    case 0:
      ownedFolder.fetch();
      break;
    case 1:
      favourites.fetch();
      break;
    case 2:
      sharedWithMe.fetch({ entity_name: "" });
      break;
    default:
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
</script>
