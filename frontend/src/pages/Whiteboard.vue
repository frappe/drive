<template>
  <div class="overflow-clip h-full w-full">
    <Tldraw
      v-if="!getWhiteboard.loading && !tlDrawAccepted"
      :draggable="false"
      :entity="entity"
      :content="content"
      @save-whiteboard="save"
    />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="entityName"
    />
    <WarningDialog v-model="tlDrawAccepted" />
  </div>
</template>
<script setup>
import { createResource } from "frappe-ui"
import {
  computed,
  defineAsyncComponent,
  inject,
  onBeforeUnmount,
  onMounted,
  ref,
} from "vue"
import { useRouter } from "vue-router"
import { useStore } from "vuex"
import { formatDate, formatSize } from "../utils/format"
import { watchDebounced } from "@vueuse/core"
import WarningDialog from "../whiteboard/WarningDialog.vue"

const Tldraw = defineAsyncComponent(() => import("../whiteboard/Tldraw.vue"))
const ShareDialog = defineAsyncComponent(() =>
  import("@/components/ShareDialog/ShareDialog.vue")
)

const content = ref(null)
const showShareDialog = ref(false)
const entity = ref(null)
const router = useRouter()
const isWritable = ref(false)
const tlDrawAccepted = ref(
  !localStorage.getItem("tldrawAccepted") ? true : false
)
const store = useStore()
const userId = computed(() => store.state.auth.user_id)
const emitter = inject("emitter")

const props = defineProps({
  entityName: {
    type: String,
    required: false,
    default: "",
  },
})

onMounted(() => {
  emitter.on("showShareDialog", () => {
    showShareDialog.value = true
  })
})

setTimeout(() => {
  watchDebounced(
    content,
    () => {
      saveDocument()
    },
    { debounce: 1500, maxWait: 30000 }
  )
}, 1500)

const saveDocument = () => {
  if (isWritable.value) {
    saveWhiteboard.submit({
      entity_name: props.entityName,
      doc_name: entity.value.document,
      title: entity.value.title,
      content: content.value,
    })
  }
}

function save(data) {
  content.value = data
}

onBeforeUnmount(() => {
  saveDocument()
})
const getWhiteboard = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  method: "GET",
  auto: true,
  params: {
    entity_name: props.entityName,
  },
  onSuccess(data) {
    data.size_in_bytes = data.file_size
    data.file_size = formatSize(data.file_size)
    data.modified = formatDate(data.modified)
    data.creation = formatDate(data.creation)
    data.owner = data.owner === userId.value ? "You" : data.owner
    isWritable.value = data.owner === userId.value || !!data.write
    content.value = data.content
    store.commit("setEntityInfo", [data])
    store.commit("setHasWriteAccess", isWritable)
    entity.value = data
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
      if (idx === data.breadcrumbs.length - 1) {
        currentBreadcrumbs.push({
          label: item.title,
          route: "/whiteboard/" + item.name,
        })
      } else {
        currentBreadcrumbs.push({
          label: item.title,
          route: "/folder/" + item.name,
        })
      }
    })
    console.log("--------------")
    console.log(currentBreadcrumbs)
    console.log("--------------")
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
})

const saveWhiteboard = createResource({
  url: "drive.api.files.save_whiteboard",
  debounce: 0,
  auto: false,
  onSuccess() {
    console.log("saved")
  },
  onError(data) {
    console.log(data)
  },
})
</script>
