<template>
  <div
    v-if="inIframe && entity"
    class="p-1.5 border-b text-base text-ink-gray-7 flex justify-between items-center relative"
  >
    <div class="font-semibold">
      {{ entity.title }}
    </div>
    <div class="flex gap-3 items-center text-ink-gray-5 text-xs">
      Edited {{ entity.relativeModified }}
    </div>
  </div>
  <Teleport
    v-if="docSettings?.doc?.settings && entity.write"
    to="#navbar-content"
    defer
  >
    <UsersBar
      v-if="editorValue?.storage?.collaborationCursor?.users?.length > 1"
      :users="editorValue.storage.collaborationCursor.users"
    />

    <Button
      v-if="docSettings?.doc?.settings?.lock"
      :icon="LucideLock"
      variant="outline"
      @click="
        () => {
          docSettings.doc.settings.lock = null
          editor.editor.commands.focus()
          toast('Unlocked document temporarily.')
        }
      "
    />
    <Button
      v-if="docSettings?.doc?.settings?.lock === null"
      :icon="LucideLockOpen"
      variant="outline"
      @click="
        () => {
          docSettings.doc.settings.lock = true
          editor.editor.commands.blur()
          toast('Locked document.')
        }
      "
    />
  </Teleport>
  <Navbar
    v-if="!inIframe && (docSettings?.doc || !isFrappeDoc)"
    :root-resource="document"
    :actions="isFrappeDoc ? navBarActions : null"
  >
    <template
      #breadcrumbs
      v-if="docSettings?.doc?.settings?.minimal && entity.write"
    >
      <Button variant="ghost">
        <router-link
          :to="$store.state.breadcrumbs?.[0]?.route"
          class="cursor-pointer"
        >
          <LucideArrowLeft class="size-3.5" />
        </router-link>
      </Button>
    </template>
  </Navbar>

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
    class="flex w-full h-full overflow-hidden"
  >
    <VersionsSidebar
      v-if="showVersions"
      v-model="current"
      v-model:show-versions="showVersions"
      :editor="editor?.editor"
      :versions="entity.versions"
      @save-document="saveDocument"
      @save-comment="saveDocument(true)"
    />
    <TextEditor
      v-if="!isFrappeDoc || docSettings?.doc?.settings"
      ref="editor"
      v-model:edited="edited"
      v-model:raw-content="rawContent"
      v-model:yjs-content="yjsContent"
      v-model:show-comments="showComments"
      v-model:current="current"
      :entity
      :editable="inIframe ? false : editable"
      :collab-turned
      :is-frappe-doc
      :settings
      :users="allUsers.data || []"
      :show-resolved
      @save-document="saveDocument"
      @new-version="
        (snap, duration, title) => {
          newVersion.submit({
            snapshot: fromUint8Array(snap),
            duration,
            title,
            manual: !!title,
          })
        }
      "
    />

    <WriterSettings
      v-if="showSettings"
      v-model="showSettings"
      :doc-settings
      :global-settings
      :editable
    />
  </div>
  <Dialog
    v-model="watermarkDialog"
    :options="{
      title: 'Add watermark',
      actions: [
        {
          label: 'Download',
          variant: 'solid',
          disabled: !watermarkConfig.text?.trim(),
          onClick: downloadWithWatermark,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          v-model="watermarkConfig.text"
          type="text"
          label="Watermark text"
          placeholder="Brand name"
          required
        />

        <FormControl
          v-model.number="watermarkConfig.size"
          type="number"
          label="Text size (px)"
          placeholder="64"
          :min="0"
          :max="300"
          :step="16"
        />

        <FormControl
          v-model.number="watermarkConfig.angle"
          type="number"
          label="Angle (°)"
          placeholder="-45"
          :min="-180"
          :max="180"
          :step="15"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { fromUint8Array, toUint8Array } from "js-base64"
import Navbar from "@/components/Navbar.vue"
import {
  ref,
  inject,
  reactive,
  defineAsyncComponent,
  provide,
  onBeforeUnmount,
  watch,
  h,
  computed,
} from "vue"
import { useStore } from "vuex"
import {
  createResource,
  LoadingIndicator,
  useDoc,
  Dialog,
  FormControl,
} from "frappe-ui"
import {
  setBreadCrumbs,
  prettyData,
  updateURLSlug,
  downloadZippedHTML,
  downloadMD
} from "@/utils/files"
import { allUsers } from "@/resources/permissions"
import VersionsSidebar from "@/components/DocEditor/components/VersionsSidebar.vue"
import WriterSettings from "@/components/DocEditor/components/WriterSettings.vue"
import { toast } from "@/utils/toasts"
import { entitiesDownload } from "@/utils/download"
import MessagesSquare from "~icons/lucide/messages-square"
import LucideRulerDimensionLine from "~icons/lucide/ruler-dimension-line"
import LucideUserPen from "~icons/lucide/user-pen"
import LucideEraser from "~icons/lucide/eraser"
import LucideView from "~icons/lucide/view"
import LucideSettings from "~icons/lucide/settings"
import LucideDownload from "~icons/lucide/download"
import LucideListRestart from "~icons/lucide/list-restart"
import LucideHistory from "~icons/lucide/history"
import MessageSquareDot from "~icons/lucide/message-square-dot"
import LucideWifi from "~icons/lucide/wifi"
import LucideLock from "~icons/lucide/lock"
import LucideLockOpen from "~icons/lucide/lock-open"
import LucideWifiOff from "~icons/lucide/wifi-off"
import LucideFileWarning from "~icons/lucide/file-warning"
import LucideFolderArchive from "~icons/lucide/folder-archive"
import LucideMarkdown from "~icons/lucide/pilcrow"
import LucideFileText from "~icons/lucide/file-text"
import { dynamicList } from "@/utils/files"
import { useTemplateRef } from "vue"
import UsersBar from "@/components/UsersBar.vue"
import { apps } from "../resources/permissions"
import LucideStamp from "~icons/lucide/stamp"
import LucideFile from "~icons/lucide/file"

const TextEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/TextEditor.vue")
)

const props = defineProps({
  entityName: String,
  slug: String,
})

const store = useStore()
const showResolved = ref(false)
const collabTurned = ref(null)
const editor = useTemplateRef("editor")
const editorValue = computed(() => editor.value?.editor)
provide("editor", editorValue)
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
const owner = computed(() => entity.value?.owner)
const isOldSchema = computed(() => {
  if (!owner.value) return false
  return (
    !docSettings?.doc?.settings?.collab && store.state.user.id !== owner.value
  )
})

const editable = computed(
  () =>
    !!entity?.value?.write &&
    !docSettings?.doc?.settings?.lock &&
    !isOldSchema.value
)
watch(showVersions, (v) => {
  if (!v) current.value = null
})
let docSettings, globalSettings
const isFrappeDoc = computed(
  () => entity.value && entity.value.mime_type === "frappe_doc"
)

const saveDocument = (comment = false) => {
  if (!edited.value || current.value) return
  if (entity.value.write || (comment && entity.value.comment)) {
    if (isFrappeDoc.value) {
      const params = {
        entity_name: props.entityName,
        doc_name: entity.value.document,
        content: rawContent.value,
        yjs: fromUint8Array(yjsContent.value || ""),
        comment,
      }
      if (docSettings.doc.settings.collab) delete params.content
      else delete params.yjs
      updateDocument.submit(params)
    } else
      updateDocument.submit({
        entity_name: props.entityName,
        content: rawContent.value,
      })
    return true
  }
}
const inIframe = inject("inIframe")

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
  setBreadCrumbs(data)
  if (data.mime_type === "frappe_doc") {
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
    globalSettings = useDoc({
      doctype: "Drive Settings",
      name: store.state.user.id,
      immediate: true,
      transform: (doc) => {
        doc.writer_settings = JSON.parse(doc.writer_settings) || {}
        return doc
      },
    })
  }
}
const settings = computed(() => {
  if (!isFrappeDoc.value) return {}
  for (const [k, v] of Object.entries(docSettings.doc?.settings || {})) {
    if (v === "global") delete docSettings.doc?.settings[k]
  }
  return {
    ...(globalSettings.doc?.writer_settings || {}),
    ...docSettings.doc?.settings,
  }
})

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
  onSuccess(data) {
    if (data && data.length != entity.value.versions.length)
      entity.value.versions = data
  },
})

// Functions and constants
const navBarActions = computed(
  () =>
    docSettings.doc && [
      "extend",
      {
        group: true,
        hideLabel: true,
        items: dynamicList([
          {
            onClick: (e) => {
              e.stopPropagation()
              e.preventDefault()
            },
            label: "Collaborate",
            icon: LucideUserPen,
            cond:
              editor.value?.editor && editor.value.editor.getText().length == 0,
            switch: true,
            switchValue: docSettings.doc.settings.collab,
            onClick: async (val) => {
              await docSettings.setValue.submit({
                settings: JSON.stringify({
                  ...docSettings.doc.settings,
                  collab: val,
                }),
              })
              $router.go()
              collabTurned.value = val
            },
          },
          {
            label: "View",
            icon: LucideView,
            cond: entity.value.write,
            submenu: [
              {
                label: "Lock",
                switch: true,
                switchValue: docSettings.doc.settings.lock,
                icon: LucideLock,
                onClick: (val) => {
                  docSettings.doc.settings.lock = val
                  docSettings.setValue.submit({
                    settings: JSON.stringify(docSettings.doc.settings),
                  })
                },
              },
              {
                label: "Wide",
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
                  docSettings.doc.settings.minimal = val
                  docSettings.setValue.submit({
                    settings: JSON.stringify(docSettings.doc.settings),
                  })
                },
                switch: true,
                switchValue: docSettings.doc.settings.minimal,
                label: "Minimal",
                icon: LucideEraser,
              },
            ],
          },
          {
            onClick: () => {
              showSettings.value = true
            },
            label: "Settings",
            icon: LucideSettings,
          },
          {
            label: "Download",
            icon: LucideDownload,
            submenu: [
              {
                label: "PDF",
                icon: LucideFile,
                onClick: () => {
                  watermarkStatus.value = false
                  entitiesDownload(null, [entity.value], watermarkStatus.value)
                },
              },
              {
                label: "PDF with Watermark",
                icon: LucideStamp,
                onClick: () => {
                  watermarkStatus.value = true
                  watermarkDialog.value = true
                },
              },
              // {
              //   label: "DOCX",
              //   icon: LucideFileText,
              // },
              {
                label: "Folder",
                icon: LucideFolderArchive,
                onClick: () => {
                  console.log(entity.value.title)
                  downloadZippedHTML(editorValue, entity.value.title)},
              },
              {
                label: "Markdown",
                icon: LucideMarkdown,
                onClick: () => {
                  console.log(entity.value.title)
                  downloadMD(editorValue, entity.value.title)},
                onClick: exportBlog,
                label: "Export Blog",
                icon: LucideImageDown,
                cond: apps.data && apps.data.find((k) => k.name === "blog"),
              },
            ],
          },
          {
            onClick: clearCache,
            label: "Clear Cache",
            icon: LucideListRestart,
          },
        ]),
      },
      {
        group: true,
        hideLabel: true,
        items: dynamicList([
          {
            icon: LucideHistory,
            label: "Versions",
            cond: docSettings?.doc?.settings.collab,
            onClick: () => (showVersions.value = true),
          },
          {
            icon: MessagesSquare,
            label: "Show Comments",
            onClick: () => (showComments.value = true),
            isEnabled: () => !showComments.value,
            cond: entity.value?.comments?.length,
          },
          {
            icon: MessagesSquare,
            label: "Hide Comments",
            onClick: () => (showComments.value = false),
            isEnabled: () => showComments,
            cond: entity.value?.comments?.length,
          },
          {
            icon: MessageSquareDot,
            label: "Show Resolved",
            onClick: () => {
              showResolved.value = true
              showComments.value = true
            },
            isEnabled: () => !showResolved.value,
            cond: entity.value?.comments?.filter((k) => k.resolved)?.length,
          },
          {
            icon: MessageSquareDot,
            label: "Hide Resolved",
            onClick: () => (showResolved.value = false),
            isEnabled: () => showResolved,
            cond: entity.value?.comments?.filter((k) => k.resolved)?.length,
          },
        ]),
      },
    ]
)

const toggleMinimal = (val) => {
  const sidebar = window.document.querySelector("#sidebar")
  if (!sidebar) return
  if (val) {
    sidebar.style.display = "none"
  } else {
    sidebar.style.removeProperty("display")
  }
}

const clearCache = () => {
  const DBDeleteRequest = window.indexedDB.deleteDatabase(
    "fdoc-" + entity.value.name
  )

  DBDeleteRequest.onerror = () => {
    console.error("Error deleting database.")
  }

  DBDeleteRequest.onsuccess = () => {
    console.log("Database deleted successfully")
  }
}

const exportMedia = async () => {
  toast("Preparing...")
  const urls = editor.value.editor.commands.getEmbedUrls()
  const getExtension = createResource({
    url: "drive.api.docs.get_extension",
  })
  for (const i in urls) {
    const ext = await getExtension.fetch({ entity_name: urls[i].name })
    if (ext) urls[i].title += "." + ext
  }
  entitiesDownload(null, urls)
}
const exportBlog = async () => {
  toast("Starting export...")
  createResource({
    url: "drive.api.docs.create_blog",
    auto: true,
    params: {
      entity_name: props.entityName,
      html: editorValue.value.getHTML(),
    },
    onSuccess: (d) => {
      window.open("/app/blog-post/" + d)
    },
    onError: (error) => {
      toast({
        title: error.messages[0] || "Could not export your document.",
        type: "error",
      })
    },
  })
}

const watermarkConfig = reactive({
  text: "",
  size: 40,
  angle: -45,
})

watch(
  watermarkConfig,
  (newObj) => {
    localStorage.setItem("watermark-obj", JSON.stringify(newObj))
  },
  { deep: true }
)

const watermarkDialog = ref(false)
const watermarkStatus = ref(false)

function downloadWithWatermark() {
  watermarkDialog.value = false
  entitiesDownload(null, [entity.value], watermarkStatus.value)
}

// Events
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

onBeforeUnmount(() => {
  if (edited.value) saveDocument()
  const sidebar = window.document.querySelector("#sidebar")
  if (sidebar) sidebar.style.removeProperty("display")
})

let toasted
watch(isOldSchema, (v) => {
  if (docSettings?.doc?.settings && entity.value.write && v && !toasted) {
    toast({
      title:
        "This document uses an old schema. Collaborative editing is disabled.",
      type: "warning",
      duration: 8000,
    })
    toasted = true
  }
})
</script>
