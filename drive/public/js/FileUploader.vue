<template>
  <!-- Body -->
  <div class="p-4 space-y-4">
    <!-- File Picker -->
    <div
      class="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-gray-500 cursor-pointer hover:border-gray-400"
      @click="triggerFileSelect"
    >
      <p v-if="!files.length">Click or drag files here to upload</p>
      <ul v-else class="text-sm w-full">
        <li v-for="file in files" :key="file.name" class="truncate">
          {{ file.name }}
        </li>
      </ul>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        multiple
        @change="onFileChange"
      />
    </div>

    <!-- Tabs (Home / Team) -->
    <div class="flex border-b space-x-4">
      <button
        v-for="(tab, idx) in tabs"
        :key="tab.label"
        @click="tabIndex = idx"
        class="pb-2 text-sm font-medium"
        :class="[
          idx === tabIndex
            ? 'border-b-2 border-blue-600 text-blue-600'
            : 'text-gray-500 hover:text-gray-700',
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Folder Tree -->
    <div class="h-48 overflow-auto">
      <ul>
        <TreeNode
          v-for="child in currentTree.children"
          :key="child.value"
          :node="child"
          :selected_node="selected_node"
          @node-click="toggle_node"
        />
      </ul>
      <div
        v-if="!currentTree.children.length"
        class="text-center text-gray-500 py-12"
      >
        No folders found
      </div>
    </div>

    <!-- Breadcrumbs -->
    <div class="flex items-center text-sm text-gray-600">
      <template v-for="(crumb, index) in breadcrumbs" :key="crumb.name">
        <button class="hover:underline" @click="closeEntity(crumb.name)">
          {{ crumb.title }}
        </button>
        <span v-if="index < breadcrumbs.length - 1" class="mx-1">/</span>
      </template>
    </div>
  </div>

  <!-- Footer -->
  <div class="flex justify-end border-t px-4 py-3">
    <button
      class="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
      :disabled="!files.length || uploading"
      @click="upload"
    >
      {{ uploading ? "Uploading..." : "Upload" }}
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import TreeNode from "./TreeNode.vue";

// props & emits
const emit = defineEmits(["success", "complete"]);

// file state
const files = ref([]);
const fileInput = ref(null);
function triggerFileSelect() {
  fileInput.value?.click();
}
function onFileChange(e) {
  files.value = Array.from(e.target.files);
}

// tabs & folder tree
const tabs = [{ label: "Home" }, { label: "Team" }];
const tabIndex = ref(0);

const homeRoot = reactive({
  label: "Home",
  value: "",
  is_group: true,
  fetching: false,
  open: true,
  children: [
    {
      label: "Heyooo",
      value: "j53da73u6v",
      is_group: true,
      fetching: false,
      open: false,
      children: [],
    },
  ],
});

const selected_node = ref(null);

const teamRoot = reactive({
  label: "Team",
  value: "",
  children: [],
});

const currentTree = computed(() =>
  tabIndex.value === 0 ? homeRoot : teamRoot
);

const currentFolder = ref("");
const breadcrumbs = ref([{ name: "", title: "Home" }]);

function closeEntity(name) {
  const idx = breadcrumbs.value.findIndex((b) => b.name === name);
  if (idx !== -1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, idx + 1);
    currentFolder.value = name;
  }
}

function toggle_node(node) {
  if (!node.fetched && node.is_group) {
    node.fetching = true;
    node.children_start = 0;
    node.children_loading = false;
    frappe
      .call("drive.api.list.files", {
        entity_name: node.value,
        team: "v384saici2",
      })
      .then(({ message }) => {
        node.open = true;
        node.children = message.map((k) => ({
          value: k.name,
          label: k.title,
          children: [],
          fetching: false,
          open: false,
          ...k,
        }));
        node.fetched = true;
        node.fetching = false;
      });
  } else {
    node.open = !node.open;
    selected_node.value = node;
    frappe
      .call("drive.api.permissions.get_entity_with_permissions", {
        entity_name: node.value,
      })
      .then(({ message }) => {
        breadcrumbs.value = [
          breadcrumbs.value[0],
          ...message.breadcrumbs.slice(1),
        ];
      });
  }
}

// upload logic (stubbed)
const uploading = ref(false);
async function upload() {
  uploading.value = true;
  // Replace with real API call
  await new Promise((r) => setTimeout(r, 1500));
  uploading.value = false;
  emit("success");
  close();
  emit("complete");
}
</script>
