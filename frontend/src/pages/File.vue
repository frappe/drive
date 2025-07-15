<template>
  <div class="flex w-full">
    <div class="w-full">
      <Navbar
        v-if="!file?.error"
        :root-resource="file"
      />
      <ErrorPage
        v-if="file.error"
        :error="file.error"
      />
      <div
        id="renderContainer"
        :draggable="false"
        class="h-[100vh] overflow-y-auto pt-8 pb-24 flex justify-center"
      >
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
        class="hidden sm:flex absolute bottom-4 left-1/2 transform -translate-x-1/2 w-fit items-center justify-center p-1 gap-1 h-10 rounded-lg shadow-xl bg-surface-white"
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
          <LucideScan class="w-4" />
        </Button>
        <Button
          :disabled="!nextEntity?.name"
          :variant="'ghost'"
          icon="arrow-right"
          @click="scrollEntity()"
        />
      </div>
    </div>

    <InfoSidebar />
  </div>
</template>

<script setup>
import { useStore } from "vuex"
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  computed,
  onMounted,
  defineProps,
  onBeforeUnmount,
  inject,
} from "vue"
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
import InfoSidebar from "@/components/InfoSidebar.vue"

const router = useRouter()
const store = useStore()
const emitter = inject("emitter")
const realtime = inject("realtime")
const props = defineProps({
  entityName: String,
  team: String,
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
}

onKeyStroke("ArrowLeft", (e) => {
  if (e.metaKey) return
  e.preventDefault()
  scrollEntity(true)
})
onKeyStroke("ArrowRight", (e) => {
  if (e.metaKey) return
  e.preventDefault()
  scrollEntity()
})

const onSuccess = async (entity) => {
  document.title = entity.title
  setBreadCrumbs(entity.breadcrumbs, entity.is_private, () =>
    emitter.emit("rename")
  )
  updateURLSlug("File", entity.title)
}

let file = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: { entity_name: props.entityName },
  transform(entity) {
    store.commit("setActiveEntity", entity)
    return prettyData([entity])[0]
  },
  onSuccess,
  onError() {
    if (!store.getters.isLoggedIn) router.push({ name: "Login" })
  },
})

function scrollEntity(negative = false) {
  currentEntity.value = negative ? prevEntity.value : nextEntity.value
  if (currentEntity.value) fetchFile(currentEntity.value.name)
}

onMounted(() => {
  fetchFile(props.entityName)
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
  realtime.doc_close("Drive File", file.data?.name)
  realtime.doc_unsubscribe("Drive File", file.data?.name)
})

let userInfo = createResource({
  url: "frappe.desk.form.load.get_user_info_for_viewers",
  // compatibility with document awareness
  onSuccess(data) {
    data = Object.values(data)
    data.forEach((item) => {
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
