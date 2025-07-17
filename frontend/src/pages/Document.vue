<template>
  <Navbar
    v-if="!document.error"
    :root-resource="document"
    :actions="[
      'extend',
      {
        icon: MessagesSquare,
        label: 'Show Comments',
        onClick: () => (showComments = true),
        isEnabled: () => !showComments,
      },
      {
        icon: MessagesSquare,
        label: 'Hide Comments',
        onClick: () => (showComments = false),
        isEnabled: () => showComments,
      },
      {
        icon: MessageSquareDot,
        label: 'Show Resolved',
        onClick: () => (showResolved = true),
        isEnabled: () => !showResolved,
      },
      {
        icon: MessageSquareDot,
        label: 'Hide Resolved',
        onClick: () => (showResolved = false),
        isEnabled: () => showResolved,
      },
    ]"
  />
  <FolderContentsError
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
      v-if="entity"
      ref="editor"
      v-model="rawContent"
      :entity="entity"
      :users="allUsers.data || []"
      :show-comments
      @save-document="saveDocument"
    />
  </div>
</template>

<script setup>
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  inject,
  onMounted,
  defineAsyncComponent,
  provide,
  onBeforeUnmount,
} from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { createResource, LoadingIndicator } from "frappe-ui"
import { setBreadCrumbs, prettyData } from "@/utils/files"
import { allUsers } from "@/resources/permissions"
import { toast } from "../utils/toasts"

import MessagesSquare from "~icons/lucide/messages-square"
import MessageSquareDot from "~icons/lucide/message-square-dot"
import LucideWifi from "~icons/lucide/wifi"
import LucideWifiOff from "~icons/lucide/wifi-off"
import LucideFileWarning from "~icons/lucide/file-warning"

const TextEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/TextEditor.vue")
)

const props = defineProps({
  entityName: String,
  team: String,
})

const store = useStore()
const route = useRoute()
const emitter = inject("emitter")
const showResolved = ref(false)
provide("showResolved", showResolved)

// Reactive data properties
const title = ref(null)
const rawContent = ref(null)
const entity = ref(null)
const lastFetched = ref(0)
const showComments = ref(false)
const edited = ref(false)

const saveDocument = () => {
  if (entity.value.write || entity.value.comment) {
    updateDocument.submit({
      entity_name: props.entityName,
      doc_name: entity.value.document,
      content: rawContent.value,
    })
    edited.value = true
    return true
  }
}

const onSuccess = (data) => {
  window.document.title = data.title
  store.commit("setActiveEntity", data)
  entity.value = data
  document.setData(prettyData([entity])[0])

  title.value = data.title
  rawContent.value = data.raw_content
  showComments.value = !!entity.value.comments.length
  lastFetched.value = Date.now()
  setBreadCrumbs(data.breadcrumbs, data.is_private, () => {
    data.write && emitter.emit("rename")
  })
}

const document = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  auto: true,
  params: {
    entity_name: props.entityName,
  },
  onSuccess,
})

const updateDocument = createResource({
  url: "drive.api.files.save_doc",
  onError(data) {
    console.log(data)
    toast({
      title: "There was an error.",
      icon: LucideFileWarning,
      text: "We can't save your file. Please contact support.",
    })
  },
})

window.addEventListener("offline", () => {
  toast({
    title: "You're offline",
    icon: LucideWifiOff,
    text: "Don't worry, your changes will be saved locally.",
  })
})
window.addEventListener("online", () => {
  toast({ title: "Back online!", icon: h(LucideWifi) })
})

onMounted(() => allUsers.fetch({ team: route.params?.team }))

onBeforeUnmount(() => edited.value && saveDocument())
</script>
