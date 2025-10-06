<template>
  <GenericPage
    :verify="currentFolder"
    :get-entities="getFolderContents"
    :empty="{
      icon: LucideFolderClosed,
      title: 'No files added yet',
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { watch, computed } from "vue"
import { useStore } from "vuex"
import { createResource } from "frappe-ui"
import { COMMON_OPTIONS } from "@/resources/files"
import {
  setBreadCrumbs,
  prettyData,
  setCache,
  updateURLSlug,
} from "@/utils/files"
import router from "@/router"
import LucideFolderClosed from "~icons/lucide/folder-closed"

const store = useStore()

const props = defineProps({
  entityName: String,
  slug: String,
})
store.commit("setCurrentFolder", { name: props.entityName })

const getFolderContents = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => ({
    ...params,
    entity_name: props.entityName,
  }),
  cache: ["folder", props.entityName],
})
setCache(getFolderContents, ["folder", props.entityName])

const onSuccess = (entity) => {
  if (router.currentRoute.value.params.entityName !== entity.name) return
  document.title = "Folder - " + entity.title
  setBreadCrumbs(entity)
  updateURLSlug(entity.title)
}

const e = computed(() => props.entityName)
const currentFolder = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  transform(entity) {
    return prettyData([entity])[0]
  },
  onSuccess,
})
store.commit("setCurrentResource", currentFolder)
watch(e, (v) => currentFolder.fetch({ entity_name: v }), { immediate: true })

const userInfo = createResource({
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
