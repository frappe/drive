<template>
  <div class="flex w-full">
    <TextEditor
      v-if="contentLoaded"
      v-model:yjsContent="yjsContent"
      v-model:rawContent="rawContent"
      v-model:settings="settings"
      :fixed-menu="true"
      :bubble-menu="true"
      placeholder="Start typing ..."
      :is-writable="isWritable"
      :entity-name="entityName"
      :entity="entity"
      @save-document="saveDocument"
    />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="entityName"
    />
  </div>
</template>

<script>
import TextEditor from "@/components/DocEditor/TextEditor.vue"
import { fromUint8Array, toUint8Array } from "js-base64"
import { formatSize, formatDate } from "@/utils/format"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"

export default {
  components: {
    TextEditor,
    ShareDialog,
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: "",
    },
  },
  data() {
    return {
      oldTitle: null,
      title: null,
      yjsContent: null,
      settings: null,
      rawContent: null,
      contentLoaded: false,
      document: null,
      isWritable: false,
      entity: null,
      beforeUnmountSaveDone: false,
      showShareDialog: false,
    }
  },
  computed: {
    titleVal() {
      return this.title ? this.title : this.oldTitle
    },
    currentFolderID() {
      return this.$store.state.currentFolderID
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
    comments() {
      return this.$store.state.allComments
    },
    userId() {
      return this.$store.state.auth.user_id
    },
  },
  mounted() {
    this.$resources.getDocument
      .fetch()
      .then(() => {
        this.title = this.$resources.getDocument.data.title
        this.oldTitle = this.$resources.getDocument.title
        this.yjsContent = this.$resources.getDocument.data.content
        this.rawContent = this.$resources.getDocument.data.raw_content
        this.document = this.$resources.getDocument.data.document
        this.isWritable =
          this.$resources.getDocument.data.owner === this.userId ||
          !!this.$resources.getDocument.data.write
        this.$store.commit("setHasWriteAccess", this.isWritable)
        this.$resources.getDocument.data.owner =
          this.$resources.getDocument.data.owner === this.userId
            ? "You"
            : this.$resources.getDocument.data.owner
        this.entity = this.$resources.getDocument.data
      })
      .then(() => {
        this.yjsContent = toUint8Array(this.$resources.getDocument.data.content)
        this.contentLoaded = true
        let currentBreadcrumbs = []
        currentBreadcrumbs = this.$store.state.currentBreadcrumbs
        if (
          !currentBreadcrumbs[currentBreadcrumbs.length - 1].route.includes(
            "/document"
          )
        ) {
          currentBreadcrumbs.push({
            label: this.title,
            route: `/document/${this.entityName}`,
          })
          this.breadcrumbs = currentBreadcrumbs
          this.$store.commit("setEntityInfo", [
            this.$resources.getDocument.data,
          ])
          this.$store.commit("setCurrentBreadcrumbs", currentBreadcrumbs)
        }
        if (this.isWritable) {
          this.timer = setInterval(() => {
            this.$resources.updateDocument.submit({
              entity_name: this.entityName,
              doc_name: this.document,
              title: this.titleVal,
              raw_content: this.rawContent,
              content: fromUint8Array(this.yjsContent),
              settings: this.settings,
              comments: this.comments,
              file_size: fromUint8Array(this.yjsContent).length,
            })
          }, 30000)
        }
      })
    this.emitter.on("showShareDialog", () => {
      this.showShareDialog = true
    })
  },
  beforeUnmount() {
    clearInterval(this.timer)
  },
  methods: {
    saveDocument() {
      if (this.isWritable) {
        this.$resources.updateDocument.submit({
          entity_name: this.entityName,
          doc_name: this.document,
          title: this.titleVal,
          content: fromUint8Array(this.yjsContent),
          raw_content: this.rawContent,
          settings: this.settings,
          comments: this.comments,
          file_size: fromUint8Array(this.yjsContent).length,
        })
      }
    },
  },
  resources: {
    updateDocument() {
      return {
        url: "drive.api.files.save_doc",
        debounce: 0,
        onError(data) {
          console.log(data)
        },
        auto: false,
      }
    },
    getDocument() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        method: "GET",
        params: {
          entity_name: this.entityName,
        },
        onSuccess(data) {
          data.size_in_bytes = data.file_size
          data.file_size = formatSize(data.file_size)
          data.modified = formatDate(data.modified)
          data.creation = formatDate(data.creation)
          this.$store.commit("setEntityInfo", [data])
          if (!data.settings) {
            data.settings =
              '{ "docWidth": false, "docSize": true, "docFont": "font-fd-sans", "docHeader": false}'
          }
          this.settings = JSON.parse(data.settings)
        },
        onError(error) {
          if (error && error.exc_type === "PermissionError") {
            this.$store.commit("setError", {
              iconName: "alert-triangle",
              iconClass: "fill-amber-500 stroke-white",
              primaryMessage: "Forbidden",
              secondaryMessage: "Insufficient permissions for this resource",
            })
          }
          this.$router.replace({ name: "Error" })
        },
        auto: false,
      }
    },
  },
}
</script>
