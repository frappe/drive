<template>
  <div class="flex w-full">
    <TextEditor
      v-if="contentLoaded"
      v-model:yjsContent="yjsContent"
      v-model:rawContent="rawContent"
      v-model:lastSaved="lastSaved"
      v-model:settings="settings"
      :user-list="allUsers"
      :fixed-menu="true"
      :bubble-menu="true"
      :timeout="timeout"
      :is-writable="isWritable"
      :entity-name="entityName"
      :entity="entity"
      @mentioned-users="(val) => (mentionedUsers = val)"
      @save-document="saveDocument"
    />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="entityName"
    />
  </div>
</template>

<script setup>
import { fromUint8Array, toUint8Array } from "js-base64"
import {
  ref,
  computed,
  inject,
  onMounted,
  defineAsyncComponent,
  onBeforeUnmount,
} from "vue"
import { useRouter } from "vue-router"
import { useStore } from "vuex"
import { formatSize, formatDate } from "@/utils/format"
import { createResource } from "frappe-ui"
import { watchDebounced } from "@vueuse/core"

const TextEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/TextEditor.vue")
)
const ShareDialog = defineAsyncComponent(() =>
  import("@/components/ShareDialog/ShareDialog.vue")
)

const store = useStore()
const router = useRouter()
const emitter = inject("emitter")

const props = defineProps({
  entityName: {
    type: String,
    required: false,
    default: "",
  },
})

// Reactive data properties
const oldTitle = ref(null)
const title = ref(null)
const yjsContent = ref(null)
const settings = ref(null)
const rawContent = ref(null)
const contentLoaded = ref(false)
const isWritable = ref(false)
const entity = ref(null)
const allUsers = ref([])
const mentionedUsers = ref()
const showShareDialog = ref(false)
const timeout = ref(1000 + Math.floor(Math.random() * 3000))
const saveCount = ref(0)
const lastSaved = ref(0)
const titleVal = computed(() => title.value || oldTitle.value)
const comments = computed(() => store.state.allComments)
const userId = computed(() => store.state.auth.user_id)

setTimeout(() => {
  watchDebounced(
    rawContent,
    () => {
      const now = Date.now()
      if (now - lastSaved.value >= timeout.value) {
        saveDocument()
      }
    },
    { debounce: timeout.value, maxWait: 30000 }
  )
}, 1500)

const saveDocument = () => {
  if (isWritable.value) {
    updateDocument.submit({
      entity_name: props.entityName,
      doc_name: entity.value.document,
      title: titleVal.value,
      content: fromUint8Array(yjsContent.value),
      raw_content: rawContent.value,
      settings: settings.value,
      comments: comments.value,
      mentions: mentionedUsers.value,
      file_size: fromUint8Array(yjsContent.value).length,
    })
  }
}

const getDocument = createResource({
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
    store.commit("setEntityInfo", [data])
    if (!data.settings) {
      data.settings =
        '{ "docWidth": false, "docSize": true, "docFont": "font-fd-sans", "docHeader": false}'
    }
    settings.value = JSON.parse(data.settings)
    title.value = data.title
    oldTitle.value = data.title
    yjsContent.value = toUint8Array(data.content)
    rawContent.value = data.raw_content
    isWritable.value = data.owner === userId.value || !!data.write
    store.commit("setHasWriteAccess", isWritable)
    data.owner = data.owner === userId.value ? "You" : data.owner
    entity.value = data
    lastSaved.value = Date.now()
    contentLoaded.value = true
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
          route: "/document/" + item.name,
        })
      } else {
        currentBreadcrumbs.push({
          label: item.title,
          route: "/folder/" + item.name,
        })
      }
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
})

const updateDocument = createResource({
  url: "drive.api.files.save_doc",
  debounce: 0,
  auto: false,
  onSuccess() {
    lastSaved.value = Date.now()
    saveCount.value++
  },
  onError(data) {
    console.log(data)
  },
})

onMounted(() => {
  emitter.on("showShareDialog", () => {
    showShareDialog.value = true
  })
})

onBeforeUnmount(() => {
  if (saveCount.value) {
    saveDocument()
  }
})

let fetchAllUsers = createResource({
  url: "drive.utils.users.get_users_with_drive_user_role_and_groups",
  method: "GET",
  auto: true,
  onSuccess(data) {
    data.forEach(function (item) {
      if (item.name) {
        item.value = item.name
        item.label = item.name
        item.type = "User Group"
        delete item.name
        return
      }
      item.value = item.email
      item.label = item.full_name.trimEnd()
      item.type = "User"
      delete item.email
      delete item.full_name
    })
    allUsers.value = data
  },
  onError(error) {
    if (error.messages) {
      this.errorMessage = error.messages.join("\n")
    } else {
      this.errorMessage = error.message
    }
  },
})
</script>
