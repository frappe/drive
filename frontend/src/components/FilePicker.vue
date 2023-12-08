<template>
  <Dialog v-model="open" :options="{ title: 'Open a file', size: '5xl' }">
    <template #body-content>
      <div class="flex" :style="{ height: 'calc(100vh - 20rem)' }">
        <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
          <NoFilesSection v-if="isEmpty" />
          <div v-else class="h-full">
            <div v-if="folders.length > 0" class="mt-3">
              <div class="text-gray-600 font-medium">Folders</div>
              <div class="flex flex-row flex-wrap gap-4 mt-4">
                <div
                  v-for="folder in folders"
                  :id="folder.name"
                  :key="folder.name"
                  class="cursor-pointer p-2 w-36 h-22 rounded-lg border group select-none entity border-gray-200 hover:shadow-2xl"
                  draggable="true"
                  @dblclick="dblClickEntity(folder)"
                  @dragenter.prevent
                  @dragover.prevent
                  @mousedown.stop>
                  <div class="flex items-start">
                    <svg
                      :style="{ fill: folder.color }"
                      :draggable="false"
                      class="h-6 w-auto"
                      viewBox="0 0 30 30"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg">
                      <path
                        d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z" />
                    </svg>
                  </div>
                  <div class="content-center grid">
                    <span class="truncate text-sm text-gray-800 mt-2">
                      {{ folder.title }}
                    </span>
                    <p class="truncate text-xs text-gray-600 mt-0">
                      {{ folder.file_size }}
                      {{ !!folder.file_size ? "∙" : null }}
                      {{ folder.modified }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div
              v-if="files.length > 0"
              :class="folders.length > 0 ? 'mt-8' : 'mt-3'">
              <div class="text-gray-600 font-medium">Files</div>
              <div class="inline-flex flex-row flex-wrap gap-4 mt-4">
                <div
                  v-for="file in files"
                  :id="file.name"
                  :key="file.name"
                  class="w-36 h-36 rounded-lg border group select-none entity cursor-pointer relative group border-gray-200 hover:shadow-2xl"
                  :draggable="false"
                  @dblclick="dblClickEntity(file)"
                  @dragenter.prevent
                  @dragover.prevent
                  @mousedown.stop>
                  <File
                    :mime_type="file.mime_type"
                    :file_ext="file.file_ext"
                    :name="file.name"
                    :title="file.title"
                    :modified="file.modified"
                    :file_size="file.file_size" />
                </div>
              </div>
            </div>
          </div>
        </Tabs>
      </div>
    </template>
  </Dialog>
</template>

<!-- 
    Grid view file picker that spits out an entity 
    Should also allow uploading a file and creating a drive entity and then spitting that out
    Also add a search bar
-->
<script setup>
import NoFilesSection from "./NoFilesSection.vue";
import File from "./File.vue";
import { watch, defineEmits, computed, h, ref, onMounted } from "vue";
import { createResource, Dialog, FeatherIcon, Button, Tabs } from "frappe-ui";
import { Clock, Star, Home, Users, Plus } from "lucide-vue-next";
import { formatSize, formatDate } from "@/utils/format";

const props = defineProps({
  title: {
    type: String,
    default: "Open a File",
  },
  suggestedTabIndex: {
    type: Number,
    default: 0,
  },
});

const tabIndex = ref(props.suggestedTabIndex);

const folderContents = ref();

watch(tabIndex, (newValue, oldValue) => {
  switch (newValue) {
    case 0:
      recents.fetch();
      break;
    case 1:
      favourites.fetch();
      break;
    case 2:
      myFiles.fetch();
      break;
    case 3:
      sharedWithMe.fetch();
      break;
    default:
      folderContents.value = [];
      break;
  }
});

const isEmpty = computed(() => {
  return folderContents.value && folderContents.value.length === 0;
});
const folders = computed(() => {
  return folderContents.value
    ? folderContents.value.filter((x) => x.is_group === 1)
    : [];
});

const files = computed(() => {
  return folderContents.value
    ? folderContents.value.filter((x) => x.is_group === 0)
    : [];
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

const tabs = [
  {
    label: "Recent",
    icon: h(Clock, { class: "w-4 h-4" }),
  },
  {
    label: "Favourite",
    icon: h(Star, { class: "w-4 h-4" }),
  },
  {
    label: "Home",
    icon: h(Home, { class: "w-4 h-4" }),
  },
  {
    label: "Shared",
    icon: h(Users, { class: "w-4 h-4" }),
  },
  {
    label: "Upload",
    icon: h(Plus, { class: "w-4 h-4" }),
  },
];

let recents = createResource({
  url: "drive.api.files.list_recents",
  method: "GET",
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

let myFiles = createResource({
  url: "drive.api.files.list_owned_entities",
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

let sharedWithMe = createResource({
  url: "drive.api.permissions.get_shared_with_me",
  method: "GET",
  auto: props.suggestedTabIndex === 3 ? true : false,
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
</script>
