<template>
  <PageGeneric
    v-if="currentFolder.fetched"
    url="drive.api.list.files"
    :allow-empty-context-menu="allowEmptyContextMenu"
    :show-sort="true"
    :is-shared-folder="isSharedFolder"
    :entity-name="entityName"
    :icon="Folder"
    :primaryMessage="'Folder is Empty'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import Folder from "../components/EspressoIcons/Folder.vue"
import PageGeneric from "@/components/PageGeneric.vue"
import { ref } from "vue"
import { useStore } from "vuex"
import { createResource } from "frappe-ui"
import { useRouter } from "vue-router"
import { formatDate } from "@/utils/format"

const store = useStore()
const router = useRouter()
const isSharedFolder = ref(false)
const allowEmptyContextMenu = ref(false)

const props = defineProps({
  entityName: {
    type: String,
    required: false,
    default: "",
  },
})

let currentFolder = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: { entity_name: props.entityName },
  transform(data) {
    if (data.owner !== store.state.auth.user_id) {
      isSharedFolder.value = true
      store.commit("setHasWriteAccess", data.write)
    } else {
      isSharedFolder.value = false
      store.commit("setHasWriteAccess", true)
    }
    let currentBreadcrumbs = store.state.currentBreadcrumbs
    // Duplicate folder in breadcrumb but unique entity ID
    const index = currentBreadcrumbs.findIndex(
      (item) => item.route === "/folder/" + props.entityName
    )
    if (index !== -1) {
      const slicedBreadCrumb = currentBreadcrumbs.slice(0, index + 1)
      store.commit("setCurrentBreadcrumbs", slicedBreadCrumb)
    } else {
      currentBreadcrumbs.push({
        label: data.title,
        route: `/folder/${props.entityName}`,
      })
      store.commit("setCurrentBreadcrumbs", currentBreadcrumbs)
    }
    data.item_count
      ? (data.file_size = data.item_count + " items")
      : delete data.file_size
    data.modified = formatDate(data.modified)
    data.creation = formatDate(data.creation)
    if (data.owner === store.state.auth.user_id) {
      allowEmptyContextMenu.value = true
      data.owner = "You"
    }
    data.write ? (allowEmptyContextMenu.value = true) : null
  },
  onSuccess(data) {
    store.commit("setCurrentFolder", [data])
    store.commit("setCurrentFolderID", props.entityName)
  },
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      store.commit("setError", {
        iconName: "alert-triangle",
        iconClass: "fill-amber-500 stroke-white",
        primaryMessage: "Forbidden",
        secondaryMessage: "Insufficient permissions for this resource",
      })
    }
    router.replace({ name: "Error" })
  },
  auto: true,
})
</script>
