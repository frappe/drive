<template>
  <div
    v-if="requiresPassword.data"
    class="mx-auto w-full bg-surface-white px-4 p-8 sm:mt-16 sm:w-112 sm:rounded-2xl sm:px-6 py-6 sm:shadow-2xl"
  >
    <div class="space-y-2">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
        This file is protected.
      </h2>
      <p class="text-gray-500 dark:text-gray-400 text-sm">
        Please enter the password to access it.
      </p>
    </div>

    <form
      @submit.prevent="
        currentFolder.fetch({ entity_name: entityName, password })
      "
      class="mt-4 space-y-4"
    >
      <FormControl
        @keydown="currentFolder.error = null"
        v-model="password"
        type="password"
        placeholder="Enter password"
        :disabled="loading"
        autofocus
      />
      <p
        v-if="currentFolder.error"
        class="text-red-500 text-sm mt-4"
      >
        {{ currentFolder.error.messages[0] }}
      </p>
      <Button
        :disabled="!password"
        :loading="loading"
        variant="solid"
        class="w-full"
        type="submit"
      >
        Unlock
      </Button>
    </form>
  </div>
  <GenericPage
    v-else
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
import { watch, computed, ref } from "vue"
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
  requiresPassword.data = false
  setBreadCrumbs(entity)
  updateURLSlug(entity.title)
}

const password = ref()
const requiresPassword = createResource({
  url: "drive.api.permissions.requires_password",
  auto: true,
  params: {
    entity_name: props.entityName,
  },
  onSuccess: (requires) =>
    !requires && currentFolder.fetch({ entity_name: params.entityName }),
})

const currentFolder = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  transform(entity) {
    return prettyData([entity])[0]
  },
  onSuccess,
})
store.commit("setCurrentResource", currentFolder)
</script>
