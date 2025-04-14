<template>
  <GenericPage
    :verify="currentFolder"
    :get-entities="getFolderContents"
    :icon="Folder"
    :primary-message="'Folder is Empty'"
  />
</template>

<script setup>
import Folder from "../components/EspressoIcons/Folder.vue"
import GenericPage from "@/components/GenericPage.vue"
import { inject, onMounted, onBeforeUnmount, watch, computed } from "vue"
import { useStore } from "vuex"
import { createResource } from "frappe-ui"
import { COMMON_OPTIONS } from "@/resources/files"
import { setBreadCrumbs, prettyData, setMetaData } from "@/utils/files"
import router from "@/router"

const store = useStore()
const realtime = inject("realtime")
const emitter = inject("emitter")

const props = defineProps({
  entityName: {
    type: String,
    required: false,
    default: "",
  },
})

const getFolderContents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => ({
    entity_name: props.entityName,
    ...params,
  }),
  cache: ["folder", props.entityName],
})

onMounted(() => {
  realtime.doc_subscribe("Drive File", props.entityName)
  realtime.doc_open("Drive File", props.entityName)
  realtime.on("doc_viewers", (data) => {
    store.state.connectedUsers = data.users
    userInfo.submit({ users: JSON.stringify(data.users) })
  })
})

onBeforeUnmount(() => {
  realtime.off("doc_viewers")
  store.state.connectedUsers = []
  realtime.doc_close("Drive File", currentFolder.data?.name)
  realtime.doc_unsubscribe("Drive File", currentFolder.data?.name)
  store.commit("setEntityInfo", [])
})

const onSuccess = (entity) => {
  if (router.currentRoute.value.params.entityName !== entity.name) return
  store.commit("setCurrentFolderID", props.entityName)
  setMetaData(entity)
  document.title = "Folder - " + entity.title
  setBreadCrumbs(entity.breadcrumbs, entity.is_private, () =>
    emitter.emit("rename")
  )
}

const e = computed(() => props.entityName)
let currentFolder = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  makeParams: (e) => ({ entity_name: e }),
  transform(entity) {
    store.commit("setCurrentFolder", [entity])
    return prettyData([entity])[0]
  },
  onSuccess,
  onError() {
    if (!store.getters.isLoggedIn) router.push({ name: "Login" })
  },
  cache: ["entity", e.value],
})
watch(e, (v) => currentFolder.fetch(v), { immediate: true })

if (currentFolder.data) {
  onSuccess(currentFolder.data)
} else {
  store.state.breadcrumbs.splice(1)
  store.state.breadcrumbs.push({ loading: true })
}

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
})
</script>
