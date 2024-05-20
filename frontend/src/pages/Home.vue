<template>
  <PageGeneric
    v-if="homeID.fetched"
    url="drive.api.list.files"
    :allow-empty-context-menu="true"
    :show-sort="true"
    :icon="Home"
    :primary-message="'Home is empty'"
    :secondary-message="'Add files by dropping them here'"
  />
</template>

<script setup>
import Home from "../components/EspressoIcons/Home.vue"
import PageGeneric from "@/components/PageGeneric.vue"
import { onMounted } from "vue"
import { createResource } from "frappe-ui"
import { useStore } from "vuex"

const store = useStore()

onMounted(() => {
  homeID.fetch()
  store.commit("setCurrentBreadcrumbs", [{ label: "Home", route: "/home" }])
})

let homeID = createResource({
  url: "drive.api.files.get_home_folder_id",
  onSuccess(data) {
    store.commit("setCurrentFolderID", data)
    store.commit("setHomeFolderID", data)
    localStorage.setItem("HomeFolderID", data)
  },
})
</script>
