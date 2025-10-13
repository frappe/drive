<template>
  <div class="flex mb-3" style="gap: 10px; align-items: center">
    Team:
    <select @change="team = $event.target.value">
      <option selected disabled>Select a team</option>
      <option
        v-for="details of teams"
        :value="details.name"
        :selected="team === details.name"
      >
        {{ details.title }}
      </option>
    </select>
  </div>
  <template v-if="team">
    <div class="flex" style="align-items: center; gap: 0.5rem">
      <input v-model="search" class="my-3" placeholder="Search" />
      <TabButtons
        :model-value="selectedTab"
        :tabs="tabs"
        @update:modelValue="selectedTab = $event"
      />
    </div>
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
      v-if="breadcrumbs.length > 1 && search.length"
      class="flex align-center text-sm text-gray-600 pt-2"
    >
      Uploading from:
      <div style="overflow: scroll; display: flex; align-items: center">
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.name">
          <span class="btn text-nowrap" @click="closeEntity(crumb.name)">
            {{ crumb.title }}
          </span>
          <span v-if="index < breadcrumbs.length - 1" class="mx-1">/</span>
        </template>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import TreeNode from "./TreeNode.vue";
import TabButtons from "./TabButtons.vue";

const emit = defineEmits(["success", "complete"]);
const tabs = [{ label: "Team" }, { label: "Public" }, { label: "Favourites" }];
const selectedTab = ref(tabs[0]);

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
    title: selectedTab.value.label,
  },
]);
const currentTree = computed(() =>
  selectedTab.value.label === "Public" ? publicRoot : teamRoot
);

const team = ref(localStorage.getItem("drive-recent-team"));

watch(
  [selectedTab, team],
  ([newValue, team]) => {
    if (!team) return;
    selected_node.value = null;
    search.value = "";
    searchResults.value = [];
    currentTree.value.searching = false;
    currentTree.value.fetching = true;
    localStorage.setItem("drive-recent-team", team);
    breadcrumbs.value = [{ name: "", title: newValue.label }];
    switch (newValue.label) {
      case "Team":
        get_files(teamRoot, "drive.api.list.files", {
          entity_name: "",
          team,
          personal: 0,
        });
        break;
      case "Public":
        get_files(publicRoot, "drive.api.list.files", {
          team,
          shared: "public",
        });
        break;
      case "Favourites":
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
  if (!query) {
    searchResults.value = [];
    currentTree.value.searching = false;
  } else {
    currentTree.value.searching = "completed";
    let { message } = await frappe.call("drive.api.list.files", {
      team: team.value,
      search: query,
      only_parent: 0,
      favourites_only: selectedTab.value.label === "Favourites" ? 1 : 0,
    });
    if (selectedTab.value.label == "Public") {
      message = message.filter((k) => k.share_count === -2);
    }
    searchResults.value = files_to_nodes(message);
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
  for (let k of out.filter((k) => k.children?.length)) {
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
        team: team.value,
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

const files_to_nodes = (arr) =>
  arr.map((k) => ({
    ...k,
    value: k.name,
    label: k.title,
    children: [],
    fetching: false,
    open: false,
  }));

const teams = ref({});
frappe
  .call("drive.api.permissions.get_teams", { details: 1 })
  .then((k) => (teams.value = k.message));

async function get_files(node, method, params) {
  const { message } = await frappe.call(method, params);
  node.open = true;
  node.children = files_to_nodes(message);
  node.fetching = false;
  node.fetched = true;
}
defineExpose({ selected_node });
</script>
<style scoped>
input,
select {
  font-size: 14px;
  line-height: 1.15;
  letter-spacing: 0.02em;
  font-weight: 420;
  padding: 0 0.5rem;
  border-radius: 0.5rem;
  border: none;
  height: 1.75rem;
  width: 100%;
  background: #f3f3f3;
}

select {
  background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="%237C7C7C" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" aria-hidden="true" viewBox="0 0 24 24" ><path d="m6 9 6 6 6-6" /></svg>');
  background-size: 1.13em;
  background-position: right 0.44rem center;
  background-repeat: no-repeat;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}

input:focus,
select:focus {
  height: 1.75rem;
  border: rgb(153, 153, 153) solid 1px;
  border-width: 1px;

  box-shadow: rgb(255, 255, 255) 0px 0px 0px 0px,
    rgb(199, 199, 199) 0px 0px 0px 2px, rgba(0, 0, 0, 0.1) 0px 1px 2px 0px;
  outline: none;
}

input:focus {
  background-color: var(--surface-white, #ffffff);
}
</style>
