<template>
  <Navbar
    v-if="!document.error"
    :root-resource="document"
  />
  <ErrorPage
    v-if="document.error"
    :error="document.error"
  />
  <LoadingIndicator
    v-else-if="!document.data && document.loading"
    :error="document.error"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <div class="flex w-full overflow-auto">
    <TextEditor
      v-if="contentLoaded"
      v-model:yjs-content="yjsContent"
      v-model:raw-content="rawContent"
      v-model:last-saved="lastSaved"
      v-model:settings="settings"
      :user-list="allUsers.data || []"
      :fixed-menu="true"
      :bubble-menu="true"
      :timeout="timeout"
      :is-writable="isWritable"
      :entity-name="entityName"
      :entity="entity"
      @mentioned-users="(val) => (mentionedUsers = val)"
      @save-document="saveDocument"
    />
  </div>
</template>

<script setup>
import { fromUint8Array, toUint8Array } from "js-base64"
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  computed,
  inject,
  onMounted,
  defineAsyncComponent,
  onBeforeUnmount,
} from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { createResource, LoadingIndicator } from "frappe-ui"
import { watchDebounced } from "@vueuse/core"
import { setBreadCrumbs, prettyData, updateURLSlug } from "@/utils/files"
import { allUsers } from "@/resources/permissions"
import router from "@/router"

const TextEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/TextEditor.vue")
)

const store = useStore()
const route = useRoute()
const emitter = inject("emitter")

const props = defineProps({
  entityName: String,
  team: String,
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
const mentionedUsers = ref([])
const timeout = ref(1000 + Math.floor(Math.random() * 1000))
const saveCount = ref(0)
const lastSaved = ref(0)
const titleVal = computed(() => title.value || oldTitle.value)
const comments = computed(() => store.state.allComments)
const userId = computed(() => store.state.user.id)
let intervalId = ref(null)

setTimeout(() => {
  watchDebounced(
    [rawContent, comments],
    () => {
      saveDocument()
    },
    {
      debounce: timeout.value,
      maxWait: 30000,
      immediate: true,
    }
  )
}, 1500)

const saveDocument = () => {
  if (isWritable.value || entity.value.comment) {
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

const onSuccess = (data) => {
  window.document.title = data.title
  updateURLSlug("Document", data.title)
  if (!data.settings) {
    data.settings =
      '{ "docWidth": false, "docSize": true, "docFont": "font-fd-sans", "docHeader": false, "docHighlightAnnotations": false, "docSpellcheck": false}'
  }
  settings.value = JSON.parse(data.settings)
  store.commit("setActiveEntity", data)

  if (!("docSpellcheck" in settings.value)) {
    settings.value.docSpellcheck = 1
  }
  document.setData(prettyData([entity])[0])
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
  setBreadCrumbs(data.breadcrumbs, data.is_private, () => {
    data.write && emitter.emit("rename")
  })
}
const document = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  method: "GET",
  auto: true,
  params: {
    entity_name: props.entityName,
  },
  onSuccess,
  onError() {
    if (!store.getters.isLoggedIn) router.push({ name: "Login" })
  },
})

const updateDocument = createResource({
  url: "drive.api.files.save_doc",
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
  allUsers.fetch({ team: route.params?.team })
  if (saveCount.value > 0) {
    intervalId.value = setInterval(() => {
      emitter.emit("triggerAutoSnapshot")
    }, 120000 + timeout.value)
  }
})

onBeforeUnmount(() => {
  if (saveCount.value) {
    saveDocument()
  }
  if (intervalId.value !== null) {
    clearInterval(intervalId.value)
  }
})
</script>
