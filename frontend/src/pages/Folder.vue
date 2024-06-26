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
      allowEmptyContextMenu.value = !!data.write
    } else {
      isSharedFolder.value = false
      store.commit("setHasWriteAccess", true)
      allowEmptyContextMenu.value = true
    }
  },
  onSuccess(data) {
    store.commit("setCurrentFolder", [data])
    store.commit("setCurrentFolderID", props.entityName)
    data.modified = formatDate(data.modified)
    data.creation = formatDate(data.creation)
    let currentBreadcrumbs = [
      {
        label: "Shared",
        route: "/shared",
      },
    ]
    const root_item = data.breadcrumbs[0]
    if (root_item.name === store.state.homeFolderID) {
      currentBreadcrumbs = [
        {
          label: "Home",
          route: "/home",
        },
      ]
      data.breadcrumbs.shift()
    }
    data.breadcrumbs.forEach((item, idx) => {
      currentBreadcrumbs.push({
        label: item.title,
        route: "/folder/" + item.name,
      })
    })
    store.commit("setCurrentBreadcrumbs", currentBreadcrumbs)
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
