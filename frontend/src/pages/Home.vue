<template>
  <PageGeneric
    v-if="!homeID.loading"
    url="drive.api.list.files"
    :allow-empty-context-menu="true"
    :entity-name="homeID.data"
    :show-sort="true"
    :icon="Home"
    :primary-message="'Home is empty'"
    :secondary-message="'Add files by dropping them here'"
  />
</template>

<script setup>
import Home from "../components/EspressoIcons/Home.vue"
import PageGeneric from "@/components/PageGeneric.vue"
import { createResource } from "frappe-ui"
import { useStore } from "vuex"

const store = useStore()

let homeID = createResource({
  url: "drive.api.files.get_home_folder_id",
  auto: true,
  onSuccess(data) {
    store.commit("setCurrentFolderID", data)
    store.commit("setHomeFolderID", data)
  },
})
</script>
