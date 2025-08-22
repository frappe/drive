<template>
  <!-- Tabs (Home / Team) -->
  <div class="flex justify-center" style="gap: 0.75rem">
    <button
      v-for="(tab, idx) in tabs"
      :key="tab.label"
      @click="tabIndex = idx"
      class="btn text-sm font-medium"
      :class="[idx === tabIndex ? 'btn-primary' : 'btn-secondary']"
    >
      {{ tab.label }}
    </button>
  </div>

  <!-- Folder Tree -->
  <div class="overflow-auto pt-3" style="height: 300px">
    <div
      v-if="currentTree.fetching"
      class="spinner-border spinner-border-sm mx-auto my-5"
    />
    <div v-else-if="!currentTree.children.length" class="text-center my-5">
      No folders found
    </div>
    <TreeNode
      v-else
      v-for="child in currentTree.children"
      :key="child.value"
      :node="child"
      class="tree-children pl-0"
      :selected_node="selected_node"
      @node-click="toggle_node"
    />
  </div>

  <!-- Breadcrumbs -->
  <div
    v-if="breadcrumbs.length > 1"
    class="flex align-center text-sm text-gray-600 pt-2"
  >
    Uploading from:
    <div style="overflow: scroll">
      <template v-for="(crumb, index) in breadcrumbs" :key="crumb.name">
        <span class="btn text-nowrap" @click="closeEntity(crumb.name)">
          {{ crumb.title }}
        </span>
        <span v-if="index < breadcrumbs.length - 1" class="mx-1">/</span>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import TreeNode from "./TreeNode.vue";

// props & emits
const emit = defineEmits(["success", "complete"]);
const tabs = [{ label: "Home" }, { label: "Team" }];
const tabIndex = ref(0);

const homeRoot = reactive({
  label: "Home",
  value: "",
  fetching: true,
  children: [],
});
const teamRoot = reactive({
  label: "Team",
  value: "",
  fetching: true,
  children: [],
});

const selected_node = ref(null);
const breadcrumbs = ref([
  {
    name: "",
    title: tabIndex.value === 0 ? "Home" : "Team",
    is_private: tabIndex.value === 0 ? 1 : 0,
  },
]);

const currentTree = computed(() =>
  tabIndex.value === 0 ? homeRoot : teamRoot
);

watch(
  tabIndex,
  (newValue) => {
    selected_node.value = "";
    currentTree.value = tabIndex.value === 0 ? homeRoot : teamRoot;
    switch (newValue) {
      case 0:
        breadcrumbs.value = [{ name: "", title: "Home", is_private: 1 }];
        get_files(homeRoot, 1);
        break;
      case 1:
        breadcrumbs.value = [{ name: "", title: "Team", is_private: 0 }];
        get_files(teamRoot, 0);
        break;
      case 2:
        folderContents.fetch({
          entity_name: "",
          favourites_only: true,
        });
        break;
    }
  },
  { immediate: true }
);

function toggle_node(node) {
  if (!node.fetched && node.is_group) {
    node.fetching = true;
    node.children_start = 0;
    node.children_loading = false;
    get_files(node);
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

async function get_files(node, personal = null) {
  const { message } = await frappe.call("drive.api.list.files", {
    entity_name: node.value,
    team: "v384saici2",
    [personal ? "personal" : ""]: personal,
  });
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
