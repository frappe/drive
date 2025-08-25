<template>
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
  <input v-model="search" class="form-control my-3" placeholder="Search" />
  <div class="overflow-auto" style="height: 300px">
    <!-- mx-auto doesn't work for some reason -->
    <div
      v-if="currentTree.fetching"
      class="flex my-5"
      style="justify-content: center"
    >
      <div class="spinner-border spinner-border-sm" />
    </div>
    <div v-else-if="!currentTree.children.length" class="text-center my-5">
      No folders found
    </div>
    <template v-else>
      <TreeNode
        v-if="searchResults.length"
        v-for="child in searchResults"
        :key="child.value"
        :node="child"
        class="tree-children pl-0"
        :selected_node="selected_node"
        @node-click="toggle_node"
      />
      <TreeNode
        v-else-if="!currentTree.searching"
        v-for="child in currentTree.children"
        :key="child.value"
        :node="child"
        class="tree-children pl-0"
        :selected_node="selected_node"
        @node-click="toggle_node"
      />
      <div v-else class="text-center my-5">
        Cannot find any files with "{{ search }}"
      </div>
    </template>
  </div>

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

const emit = defineEmits(["success", "complete"]);
const tabs = [{ label: "Home" }, { label: "Team" }, { label: "Favourites" }];
const tabIndex = ref(1);

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
const searchResults = ref([]);
const search = ref("");
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
    selected_node.value = null;
    console.log(newValue);
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
        breadcrumbs.value = [{ name: "", title: "Favourites" }];
        get_files(teamRoot, -1, 1);
        break;
    }
  },
  { immediate: true }
);

watch(search, (val) => {
  let reg = new RegExp(val, "i");
  if (!val) {
    searchResults.value = [];
    currentTree.value.searching = false;
  } else {
    currentTree.value.searching = true;
    searchResults.value = recursiveSearch(currentTree.value, reg);
  }
});

const bisect = (arr, cond) => {
  let res1 = [];
  let res2 = [];
  for (k of arr) {
    if (cond(k)) res1.push(k);
    else res2.push(k);
  }
  return [res1, res2];
};
const recursiveSearch = (node, reg) => {
  const [res, out] = bisect(node.children, (k) => reg.test(k.title));
  for (let k of out) {
    if (k.children?.length) res.push(...recursiveSearch(k, reg));
  }
  return res;
};

function toggle_node(node) {
  if (node.is_group) {
    if (!node.fetched) {
      node.fetching = true;
      node.children_start = 0;
      node.children_loading = false;
      get_files(node);
    } else {
      node.open = !node.open;
    }
  } else {
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

async function get_files(node, personal = null, favourites = 0) {
  const { message } = await frappe.call("drive.api.list.files", {
    entity_name: node.value,
    team: "v384saici2",
    [personal ? "personal" : ""]: personal,
    favourites_only: favourites,
  });
  node.open = true;
  node.children = message.map((k) => ({
    ...k,
    value: k.name,
    label: k.title,
    children: [],
    fetching: false,
    open: false,
  }));
  node.fetching = false;
  node.fetched = true;
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

defineExpose({ selected_node });
</script>
