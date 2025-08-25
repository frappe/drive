<template>
  <Navbar
    v-if="!document.error"
    :root-resource="document"
    :actions="
      dynamicList([
        'extend',
        {
          onClick: (e) => {
            e.stopPropagation()
            e.preventDefault()
          },
          component: h(Switch, {
            label: 'Collaborate',
            icon: LucideUserRoundPen,
            modelValue: docSettings && docSettings.doc?.settings?.collab,
            'onUpdate:modelValue': (val) => {
              docSettings.doc.settings.collab = val
              docSettings.setValue.submit({
                settings: JSON.stringify(docSettings.doc.settings),
              })
              if (val) {
                // Used to rerender text editor when collab is toggled
                switchCount++
              } else {
                switchCount = 0
              }
            },
          }),
        },
        {
          icon: MessagesSquare,
          label: 'Show Comments',
          onClick: () => (showComments = true),
          isEnabled: () => !showComments,
          cond: entity?.comments?.length,
        },
        {
          icon: MessagesSquare,
          label: 'Hide Comments',
          onClick: () => (showComments = false),
          isEnabled: () => showComments,
          cond: entity?.comments?.length,
        },
        {
          icon: MessageSquareDot,
          label: 'Show Resolved',
          onClick: () => {
            showResolved = true
            showComments = true
          },
          isEnabled: () => !showResolved,
          cond: entity?.comments?.filter((k) => k.resolved)?.length,
        },
        {
          icon: MessageSquareDot,
          label: 'Hide Resolved',
          onClick: () => (showResolved = false),
          isEnabled: () => showResolved,
          cond: entity?.comments?.filter((k) => k.resolved)?.length,
        },
      ])
    "
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
  <div
    v-else
    class="flex w-full h-full overflow-auto"
  >
    <TextEditor
      v-if="entity && docSettings"
      :key="switchCount"
      ref="editor"
      v-model:edited="edited"
      v-model:raw-content="rawContent"
      v-model:yjs-content="yjsContent"
      v-model:show-comments="showComments"
      :settings="docSettings.doc?.settings"
      :entity="entity"
      :users="allUsers.data || []"
      :show-resolved
      @save-document="saveDocument"
    />
  </div>
</template>

<script setup>
import { fromUint8Array, toUint8Array } from "js-base64"
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  inject,
  onMounted,
  defineAsyncComponent,
  provide,
  onBeforeUnmount,
  h,
  computed,
  reactive,
} from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { createResource, LoadingIndicator, Switch, useDoc } from "frappe-ui"
import { setBreadCrumbs, prettyData, updateURLSlug } from "@/utils/files"
import { allUsers } from "@/resources/permissions"
import { toast } from "../utils/toasts"

import MessagesSquare from "~icons/lucide/messages-square"
import LucideUserRoundPen from "~icons/lucide/user-round-pen"
import MessageSquareDot from "~icons/lucide/message-square-dot"
import LucideWifi from "~icons/lucide/wifi"
import LucideWifiOff from "~icons/lucide/wifi-off"
import LucideFileWarning from "~icons/lucide/file-warning"
import { dynamicList } from "../utils/files"
import { useTemplateRef } from "vue"

const TextEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/TextEditor.vue")
)

const props = defineProps({
  entityName: String,
  team: String,
  slug: String,
})

const store = useStore()
const route = useRoute()
const emitter = inject("emitter")
const showResolved = ref(false)
const switchCount = ref(0)
const editor = useTemplateRef("editor")
provide(
  "editor",
  computed(() => editor.value.editor)
)
provide("showResolved", showResolved)

// Reactive data properties
const title = ref(null)
const rawContent = ref(null)
const yjsContent = ref(null)
const entity = ref(null)
const lastFetched = ref(0)
const showComments = ref(false)
const edited = ref(false)

let docSettings

const saveDocument = () => {
  if (entity.value.write || entity.value.comment) {
    updateDocument.submit({
      entity_name: props.entityName,
      doc_name: entity.value.document,
      content: rawContent.value,
      yjs: fromUint8Array(yjsContent.value),
    })
    edited.value = true
    return true
  }
}

const onSuccess = (data) => {
  window.document.title = data.title
  updateURLSlug(data.title)

  document.setData(prettyData([data])[0])
  entity.value = data
  store.commit("setActiveEntity", data)

  title.value = data.title
  rawContent.value = data.raw_content
  yjsContent.value = toUint8Array(data.content)
  lastFetched.value = Date.now()
  docSettings = useDoc({
    doctype: "Drive Document",
    name: data.document,
    immediate: true,
  })
  docSettings.onSuccess((doc) => (doc.settings = JSON.parse(doc.settings)))
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
store.commit("setCurrentResource", document)

const updateDocument = createResource({
  url: "drive.api.files.save_doc",
  onError(error) {
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
