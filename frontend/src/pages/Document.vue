<template>
  <Teleport
    v-if="docSettings?.doc?.settings?.minimal && entity.write"
    to="#navbar-prefix"
    defer
  >
    <router-link
      :to="originalBreadcrumbs?.[0]?.route"
      class="cursor-pointer"
    >
      <LucideArrowLeft class="size-3.5" />
    </router-link>
  </Teleport>
  <Teleport
    v-if="docSettings?.doc?.settings && entity.write"
    to="#navbar-content"
    defer
  >
    <Button
      v-if="docSettings?.doc?.settings?.lock"
      :icon="LucideLock"
      @click="
        () => {
          docSettings.doc.settings.lock = null
          editor.editor.commands.focus()
          toast('Unlocked document temporarily.')
        }
      "
      variant="outline"
    />
    <Button
      v-if="docSettings?.doc?.settings?.lock === null"
      :icon="LucideLockOpen"
      @click="
        () => {
          docSettings.doc.settings.lock = true
          editor.editor.commands.blur()
          toast('Locked document.')
        }
      "
      variant="outline"
    />
  </Teleport>
  <Navbar
    v-if="!document.error && docSettings?.doc"
    :root-resource="document"
    :actions="[
      'extend',
      {
        group: true,
        hideLabel: true,
        items: dynamicList([
          {
            onClick: (e) => {
              e.stopPropagation()
              e.preventDefault()
            },
            label: 'Collaborate',
            icon: LucideUserPen,
            switch: true,
            switchValue: docSettings.doc.settings.collab,
            onClick: (val) => {
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
          },
          {
            label: 'View',
            icon: LucideView,
            cond: entity.write,
            submenu: [
              {
                label: 'Lock',
                switch: true,
                switchValue: docSettings.doc.settings.lock,
                icon: LucideLock,
                onClick: (val) => {
                  console.log(val)
                  docSettings.doc.settings.lock = val
                  docSettings.setValue.submit({
                    settings: JSON.stringify(docSettings.doc.settings),
                  })
                },
              },
              {
                label: 'Wide',
                icon: LucideRulerDimensionLine,
                switch: true,
                switchValue: docSettings.doc.settings.wide,
                onClick: (val) => {
                  docSettings.doc.settings.wide = val
                  docSettings.setValue.submit({
                    settings: JSON.stringify(docSettings.doc.settings),
                  })
                },
              },
              {
                onClick: (val) => {
                  document.breadcrumbs = []
                  docSettings.doc.settings.minimal = val
                  docSettings.setValue.submit({
                    settings: JSON.stringify(docSettings.doc.settings),
                  })
                },
                switch: true,
                switchValue: docSettings.doc.settings.minimal,
                label: 'Minimal',
                icon: LucideEraser,
              },
            ],
          },
          {
            onClick: () => {
              showSettings = true
            },
            label: 'Settings',
            icon: LucideSettings,
          },
        ]),
      },
      {
        group: true,
        hideLabel: true,
        items: dynamicList([
          {
            icon: MessagesSquare,
            label: 'Versions',
            onClick: () => (showVersions = true),
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
        ]),
      },
    ]"
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
      ref="editor"
      v-model:edited="edited"
      v-model:raw-content="rawContent"
      v-model:yjs-content="yjsContent"
      v-model:show-comments="showComments"
      v-model:current="current"
      :entity
      :editable
      :settings="docSettings?.doc?.settings"
      :users="allUsers.data || []"
      :show-resolved
      @save-document="saveDocument"
      @new-version="
        (snap) => {
          newVersion.submit({
            snapshot: fromUint8Array(snap),
          })
        }
      "
    />
    <VersionsSidebar
      v-if="showVersions"
      v-model="current"
      v-model:show-versions="showVersions"
      :editor="editor?.editor"
      :versions="entity.versions"
      @save-document="saveDocument"
      @save-comment="saveDocument(true)"
    />
    <WriterSettings
      v-if="showSettings"
      v-model="showSettings"
      :doc-settings
      :editable
    />
  </div>
</template>

<script setup>
import { fromUint8Array, toUint8Array } from "js-base64"
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  inject,
  defineAsyncComponent,
  provide,
  onBeforeUnmount,
  watch,
  h,
  computed,
} from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { createResource, LoadingIndicator, Switch, useDoc } from "frappe-ui"
import { setBreadCrumbs, prettyData, updateURLSlug } from "@/utils/files"
import { allUsers } from "@/resources/permissions"
import VersionsSidebar from "@/components/DocEditor/components/VersionsSidebar.vue"
import WriterSettings from "@/components/DocEditor/components/WriterSettings.vue"
import { toast } from "../utils/toasts"

import MessagesSquare from "~icons/lucide/messages-square"
import LucideRulerDimensionLine from "~icons/lucide/ruler-dimension-line"
import LucideUserPen from "~icons/lucide/user-pen"
import LucideEraser from "~icons/lucide/eraser"
import LucideView from "~icons/lucide/view"
import LucideSettings from "~icons/lucide/settings"
import MessageSquareDot from "~icons/lucide/message-square-dot"
import LucideWifi from "~icons/lucide/wifi"
import LucideLock from "~icons/lucide/lock"
import LucideLockOpen from "~icons/lucide/lock-open"
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
const test = ref(true)
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
const current = ref(null)
const lastFetched = ref(0)
const showComments = ref(false)
const showVersions = ref(false)
const showSettings = ref(false)
const edited = ref(false)
const editable = computed(
  () => !!entity?.value?.write && !docSettings?.doc?.settings?.lock
)
watch(showVersions, (v) => {
  if (!v) current.value = null
})

let docSettings

const saveDocument = (comment = false) => {
  if (entity.value.write || (comment && entity.value.comment)) {
    if (entity.value.mime_type === "frappe_doc")
      updateDocument.submit({
        entity_name: props.entityName,
        doc_name: entity.value.document,
        content: rawContent.value,
        yjs: fromUint8Array(yjsContent.value),
      })
    else
      updateDocument.submit({
        entity_name: props.entityName,
        content: rawContent.value,
        comment,
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
  if (data.content) yjsContent.value = toUint8Array(data.content)
  lastFetched.value = Date.now()
  setBreadCrumbs(data.breadcrumbs, data.is_private, () => {
    data.write && emitter.emit("rename")
  })
  if (data.mime_type === "frappe_doc")
    docSettings = useDoc({
      doctype: "Drive Document",
      name: data.document,
      immediate: true,
      transform: (doc) => {
        doc.settings = JSON.parse(doc.settings)
        if (entity.value.write) toggleMinimal(doc.settings.minimal)
        return doc
      },
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
  onError() {
    toast({
      title: "There was an error.",
      icon: LucideFileWarning,
      text: "We can't save your file. Please contact support.",
    })
  },
})

const newVersion = createResource({
  url: "drive.api.docs.create_version",
  makeParams: (k) => ({ ...k, doc: entity.value.document }),
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

allUsers.fetch({ team: route.params.team })

onBeforeUnmount(() => {
  if (edited.value) saveDocument()
  window.document.querySelector("#sidebar").style.removeProperty("display")
})

let originalBreadcrumbs
const toggleMinimal = (val) => {
  if (val) {
    originalBreadcrumbs = [...store.state.breadcrumbs]
    store.commit("setBreadcrumbs", store.state.breadcrumbs.slice(-1))
    window.document.querySelector("#sidebar").style.display = "none"
  } else if (originalBreadcrumbs) {
    store.commit("setBreadcrumbs", originalBreadcrumbs)
    window.document.querySelector("#sidebar").style.removeProperty("display")
  }
}
</script>
