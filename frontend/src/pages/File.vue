<template>
  <div class="flex w-full h-full">
    <div class="w-full h-full flex flex-col">
      <Navbar
        v-if="!file?.error"
        :root-resource="file"
      />
      <ErrorPage
        v-if="file.error"
        :error="file.error"
      />
      <div
        v-else
        id="renderContainer"
        :draggable="false"
        class="w-full p-10 flex-grow w-full flex justify-center align-center items-center relative"
      >
        <Button
          class="text-ink-gray-8 absolute top-4 left-4"
          :variant="'ghost'"
          icon="arrow-left"
          @click="closePreview"
        />
        <LoadingIndicator
          v-if="file.loading"
          class="w-10 h-full text-neutral-100"
        />
        <FileRender
          v-else-if="file.data"
          :preview-entity="file.data"
        />
      </div>
      <div
        class="hidden sm:flex absolute bottom-4 left-1/2 transform -translate-x-1/2 w-fit items-center justify-center p-1 gap-1 rounded shadow-xl l bg-surface-white"
      >
        <Button
          :disabled="!prevEntity?.name"
          :variant="'ghost'"
          icon="arrow-left"
          @click="scrollEntity(true)"
        />
        <Button
          :variant="'ghost'"
          @click="enterFullScreen"
        >
          <LucideScan class="size-4" />
        </Button>
        <Button
          :disabled="!nextEntity?.name"
          :variant="'ghost'"
          icon="arrow-right"
          @click="scrollEntity()"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useStore } from "vuex"
import Navbar from "@/components/Navbar.vue"
import { ref, computed, onMounted, defineProps } from "vue"
import { Button, LoadingIndicator } from "frappe-ui"
import FileRender from "@/components/FileRender.vue"
import { createResource } from "frappe-ui"
import { useRouter } from "vue-router"
import LucideScan from "~icons/lucide/scan"
import { onKeyStroke } from "@vueuse/core"
import {
  prettyData,
  setBreadCrumbs,
  enterFullScreen,
  updateURLSlug,
} from "@/utils/files"
import ErrorPage from "@/components/ErrorPage.vue"

const router = useRouter()
const store = useStore()
const props = defineProps({
  entityName: String,
  slug: String,
})

const currentEntity = ref(props.entityName)

const filteredEntities = computed(() =>
  store.state.currentFolder.entities.filter(
    (item) => !item.is_group && !item.document && !item.is_link
  )
)

const index = computed(() => {
  return filteredEntities.value.findIndex(
    (item) => item.name === props.entityName
  )
})
const prevEntity = computed(() => filteredEntities.value[index.value - 1])
const nextEntity = computed(() => filteredEntities.value[index.value + 1])

function fetchFile(currentEntity) {
  file.fetch({ entity_name: currentEntity })
  router.push({
    params: {
      entityName: currentEntity,
    },
  })
}

onKeyStroke("ArrowLeft", (e) => {
  if (!e.shiftKey) return
  e.preventDefault()
  scrollEntity(true)
})
onKeyStroke("ArrowRight", (e) => {
  if (!e.shiftKey) return
  e.preventDefault()
  scrollEntity()
})

const onSuccess = async (entity) => {
  document.title = entity.title
  setBreadCrumbs(entity)
  updateURLSlug(entity.title)
}

const file = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: { entity_name: props.entityName },
  onSuccess(data) {
    if (data.redirect) {
      router.push(data.route)
      return
    }
    store.commit("setActiveEntity", data)
    const prettyEntity = prettyData([data])[0]
    file.setData(prettyEntity)
    onSuccess(prettyEntity)
  },
})
store.commit("setCurrentResource", file)

function scrollEntity(negative = false) {
  currentEntity.value = negative ? prevEntity.value : nextEntity.value
  if (currentEntity.value) fetchFile(currentEntity.value.name)
}

function closePreview() {
  router.push({
    name: "Folder",
    params: { entityName: file.data.parent_entity },
  })
}

onMounted(() => {
  fetchFile(props.entityName)
})
</script>

<style scoped>
.center-transform {
  transform: translate(-50%, -50%);
}

#renderContainer::backdrop {
  background-color: rgb(0, 0, 0);
  min-width: 100vw;
  min-height: 100vh;
  position: fixed;
  width: 100%;
  height: 100%;
  left: 0;
  top: 0;
}
</style>
