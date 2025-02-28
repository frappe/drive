<template>
  <GenericPage
    v-if="currentFolder.fetched"
    :get-entities="getFolderContents"
    :icon="Folder"
    :primary-message="'Folder is Empty'"
  />
</template>

<script setup>
import Folder from "../components/EspressoIcons/Folder.vue"
import GenericPage from "@/components/GenericPage.vue"
import { inject, onMounted, onBeforeUnmount } from "vue"
import { useStore } from "vuex"
import { createResource } from "frappe-ui"
import { useRouter } from "vue-router"
import { formatDate } from "@/utils/format"
import { getFolderContents } from "@/resources/files"
import { setBreadCrumbs, prettyData } from "../utils/files"

const store = useStore()
const router = useRouter()
const realtime = inject("realtime")

const props = defineProps({
  entityName: {
    type: String,
    required: false,
    default: "",
  },
})
getFolderContents.reset()
getFolderContents.update({
  params: {
    entity_name: props.entityName,
  },
  cache: "folder-" + props.entityName,
})

onMounted(() => {
  realtime.doc_subscribe("Drive File", props.entityName)
  realtime.doc_open("Drive File", props.entityName)
  realtime.on("doc_viewers", (data) => {
    store.state.connectedUsers = data.users
    userInfo.submit({ users: JSON.stringify(data.users) })
  })
  if (window.matchMedia("(max-width: 1500px)").matches) {
    store.commit("setIsSidebarExpanded", false)
  }
})

onBeforeUnmount(() => {
  realtime.off("doc_viewers")
  store.state.connectedUsers = []
  realtime.doc_close("Drive File", currentFolder.data?.name)
  realtime.doc_unsubscribe("Drive File", currentFolder.data?.name)
  store.commit("setEntityInfo", [])
})

let currentFolder = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: { entity_name: props.entityName },
  transform(entity) {
    store.commit("setCurrentFolder", [entity])
    store.commit("setCurrentFolderID", props.entityName)
    entity = prettyData([entity])
  },
  onSuccess(data) {
    data.modified = formatDate(data.modified)
    data.creation = formatDate(data.creation)
    setBreadCrumbs(data.breadcrumbs, data.is_private, false)
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

let userInfo = createResource({
  url: "frappe.desk.form.load.get_user_info_for_viewers",
  onSuccess(data) {
    data = Object.values(data)
    data.forEach((item) => {
      // compatibility with document awareness
      if (item.fullname) {
        item.avatar = item.image
        item.name = item.fullname
        delete item.image
        delete item.fullname
      }
    })
    store.state.connectedUsers = data
  },
  auto: false,
})
</script>
