<template>
  <GenericPage
    :verify="currentFolder"
    :get-entities="getFolderContents"
    v-model:order-by="orderBy"
    :id="entityName"
    :empty="{
      icon: LucideFolderClosed,
      title: 'No files added yet',
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { watch, computed, ref } from "vue"
import { useStore } from "vuex"
import { createResource, useList } from "frappe-ui"
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

const orderBy = ref(
  store.state.sortOrder[props.entityName] || {
    label: "Modified",
    field: "modified",
    ascending: false,
  }
)
const getFolderContents = useList({
  ...COMMON_OPTIONS,
  url: "/api/method/drive.api.list.files",
  parent: props.entityName,
  orderBy: orderBy.value.field + (orderBy.value.ascending ? " 1" : " 0"),
  immediate: false,
  limit: 100,
  // cacheKey: ["folder", props.entityName],
})
// setCache(getFolderContents, ["folder", props.entityName])

const onSuccess = (entity) => {
  console.log(store.state.sortOrder)
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
</script>
