<template>
  <Navbar />
  <FolderContentsError v-if="file.error" :error="file.error" />
  <LoadingIndicator
    v-if="file.loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <div
    v-else
    class="h-full w-full overflow-hidden flex flex-col items-center justify-start"
  >
    <div
      id="renderContainer"
      :draggable="false"
      class="flex items-center justify-center h-full w-full min-h-[85vh] max-h-[85vh] mt-3"
    >
      <FileRender v-if="file.data" :preview-entity="file.data" />
    </div>
    <div
      class="hidden sm:flex absolute bottom-[-1%] left-[50%] center-transform items-center justify-center p-1 gap-1 h-10 rounded-lg shadow-xl bg-white"
    >
      <Button
        :disabled="!prevEntity?.name"
        :variant="'ghost'"
        icon="arrow-left"
        @click="scrollEntity(true)"
      ></Button>
      <Button :variant="'ghost'" @click="enterFullScreen">
        <Scan class="w-4" />
      </Button>
      <Button
        :disabled="!nextEntity?.name"
        :variant="'ghost'"
        icon="arrow-right"
        @click="scrollEntity()"
      ></Button>
    </div>
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
import { Scan } from "lucide-vue-next"
import { onKeyStroke } from "@vueuse/core"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"
import { prettyData, setBreadCrumbs, setMetaData } from "@/utils/files"
import FolderContentsError from "@/components/FolderContentsError.vue"

const router = useRouter()
const store = useStore()
const emitter = inject("emitter")
const realtime = inject("realtime")
const props = defineProps({
  entityName: {
    type: String,
    default: null,
  },
})

const dialog = ref("")
const currentEntity = ref(props.entityName)

const filteredEntities = computed(() => {
  console.log(store.state.currentEntitites)
  if (store.state.currentEntitites.length) {
    return store.state.currentEntitites.filter(
      (item) => item.is_group === 0 && item.mime_type !== "frappe_doc"
    )
  } else {
    return []
  }
})

const index = computed(() => {
  return filteredEntities.value.findIndex(
    (item) => item.name === props.entityName
  )
})
const prevEntity = computed(() => filteredEntities.value[index.value - 1])
const nextEntity = computed(() => filteredEntities.value[index.value + 1])

function fetchFile(currentEntity) {
  file.fetch({ entity_name: currentEntity }).then(() => {
    router.replace({
      name: "File",
      params: { entityName: currentEntity },
    })
  })
}

function enterFullScreen() {
  let elem = document.getElementById("renderContainer")
  if (elem.requestFullscreen) {
    elem.requestFullscreen()
  } else if (elem.mozRequestFullScreen) {
    /* Firefox */
    elem.mozRequestFullScreen()
  } else if (elem.webkitRequestFullscreen) {
    /* Chrome, Safari & Opera */
    elem.webkitRequestFullscreen()
  } else if (elem.msRequestFullscreen) {
    /* IE/Edge */
    elem.msRequestFullscreen()
  }
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

const onSuccess = (entity) => {
  setMetaData(entity)
  setBreadCrumbs(entity.breadcrumbs, entity.is_private, () =>
    emitter.emit("rename")
  )
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
  emitter.on("showShareDialog", () => {
    dialog.value = "s"
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
