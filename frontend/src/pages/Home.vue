<template>
  <PageGeneric
    v-if="homeID.fetched"
    url="drive.api.files.list_owned_entities"
    :allowEmptyContextMenu="true"
    :showSort="true" />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue";
import { onMounted } from "vue";
import { createResource } from "frappe-ui";
import { useStore } from "vuex";

const store = useStore();

onMounted(() => {
  homeID.fetch();
  store.commit("setCurrentBreadcrumbs", [{ label: "Home", route: "/home" }]);
});

let homeID = createResource({
  url: "drive.api.files.get_home_folder_id",
  onSuccess(data) {
    store.commit("setCurrentFolderID", data);
    store.commit("setHomeFolderID", data);
    localStorage.setItem("HomeFolderID", data);
  },
});
</script>
