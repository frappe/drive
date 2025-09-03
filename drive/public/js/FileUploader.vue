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
const tabs = [{ label: "Team" }, { label: "Public" }, { label: "Favourites" }];
const tabIndex = ref(1);

const teamRoot = reactive({
  label: "Team",
  value: "",
  fetching: true,
  children: [],
});
const publicRoot = reactive({
  label: "Public",
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
    title: tabIndex.value === 0 ? "Team" : "Public",
  },
]);
const currentTree = computed(() =>
  tabIndex.value === 1 ? publicRoot : teamRoot
);

watch(
  tabIndex,
  (newValue) => {
    selected_node.value = null;
    switch (newValue) {
      case 0:
        breadcrumbs.value = [{ name: "", title: "Team" }];
        get_files(teamRoot, "drive.api.list.files", {
          entity_name: "",
          team,
          personal: 0,
        });
        break;
      case 1:
        breadcrumbs.value = [{ name: "", title: "Public" }];
        get_files(publicRoot, "drive.api.list.shared", {
          team,
          public: 1,
        });
        break;
      case 2:
        breadcrumbs.value = [{ name: "", title: "Favourites" }];
        get_files(teamRoot, "drive.api.list.files", {
          entity_name: "",
          team,
          favourites_only: 1,
        });
        break;
    }
  },
  { immediate: true }
);

watch(search, async (query) => {
  let reg = new RegExp(query, "i");
  if (!query) {
    searchResults.value = [];
    currentTree.value.searching = false;
  } else {
    currentTree.value.searching = "searching";
    const res = recursiveSearch(currentTree.value, reg);
    // don't global search for favourites
    if (res.length || tabIndex.value === 2) {
      currentTree.value.searching = "completed";
      searchResults.value = res;
    } else {
      const { message } = await frappe.call("drive.api.files.search", {
        team,
        query,
      });
      searchResults.value = files_to_nodes(message);
    }
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
      get_files(node, "drive.api.list.files", {
        entity_name: node.value,
        team,
      });
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

const team = "v384saici2";
const files_to_nodes = (arr) =>
  arr.map((k) => ({
    ...k,
    value: k.name,
    label: k.title,
    children: [],
    fetching: false,
    open: false,
  }));

async function get_files(node, method, params) {
  const { message } = await frappe.call(method, params);
  node.open = true;
  node.children = files_to_nodes(message);
  node.fetching = false;
  node.fetched = true;
}
defineExpose({ selected_node });
</script>
