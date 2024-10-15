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
import { useRouter } from "vue-router"

const store = useStore()
const router = useRouter()

let homeID = createResource({
  url: "drive.api.files.get_home_folder_id",
  auto: true,
  onSuccess(data) {
    store.commit("setCurrentFolderID", data)
    store.commit("setHomeFolderID", data)
  },
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      store.commit("setError", {
        iconName: "alert-triangle",
        iconClass: "fill-amber-500 stroke-white",
        primaryMessage: "Forbidden",
        secondaryMessage: "You do not have access to Frappe Drive",
        hideButton: true,
      })
      if (store.state.user.role === "Drive Guest") {
        router.replace({ name: "Recents" })
      } else {
        router.replace({ name: "Error" })
      }
    }
  },
})
</script>
