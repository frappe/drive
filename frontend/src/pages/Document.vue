<template>
  <TextEditor
    v-if="contentLoaded"
    v-model="content"
    :fixed-menu="true"
    :bubble-menu="true"
    placeholder="Start typing ..."
    :isWritable="isWriteable"
    :entityName="entityName"
    :entity="entity"
    @saveDocument="saveDocument" />
</template>

<script>
import TextEditor from "@/components/DocEditor/TextEditor.vue";
import { fromUint8Array, toUint8Array } from "js-base64";
import { toast } from "../utils/toasts";
import { formatSize, formatDate } from "@/utils/format";

export default {
  components: {
    TextEditor,
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
      content: null,
      contentLoaded: false,
      document: null,
      isWriteable: false,
      entity: null,
      beforeUnmountSaveDone: false,
    };
  },

  computed: {
    titleVal() {
      return this.title ? this.title : this.oldTitle;
    },
    currentFolderID() {
      return this.$store.state.currentFolderID;
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    comments() {
      return this.$store.state.allComments;
    },
    userId() {
      return this.$store.state.auth.user_id;
    },
  },
  methods: {
    saveDocument() {
      this.$resources.updateDocument.submit({
        entity_name: this.entityName,
        doc_name: this.document,
        title: this.titleVal,
        content: fromUint8Array(this.content),
        comments: this.comments,
        file_size: fromUint8Array(this.content).length,
      });
      if (
        this.entity.title.includes("Untitled Document") &&
        this.entity.title != this.$store.state.entityInfo[0].title
      ) {
        this.$resources.rename.submit({
          method: "rename",
          entity_name: this.entityName,
          new_title: this.$store.state.entityInfo[0].title,
        });
      }
      toast({
        title: "Document saved",
        position: "bottom-right",
        timeout: 2,
      });
    },
    async saveAndRenameDocument() {
      if (
        this.entity.title.includes("Untitled Document") &&
        this.entity.title != this.$store.state.entityInfo[0].title
      ) {
        await this.$resources.rename
          .submit({
            method: "rename",
            entity_name: this.entityName,
            new_title: this.$store.state.entityInfo[0].title,
          })
          .then(() => {
            this.$resources.updateDocument.submit({
              entity_name: this.entityName,
              doc_name: this.document,
              title: this.$store.state.entityInfo[0].title,
              content: fromUint8Array(this.content),
              comments: this.comments,
              file_size: fromUint8Array(this.content).length,
            });
            this.beforeUnmountSaveDone = true;
          });
      } else {
        await this.$resources.updateDocument.submit({
          entity_name: this.entityName,
          doc_name: this.document,
          title: this.$store.state.entityInfo[0].title,
          content: fromUint8Array(this.content),
          comments: this.comments,
          file_size: fromUint8Array(this.content).length,
        });
        this.beforeUnmountSaveDone = true;
      }
    },
  },
  mounted() {
    this.$resources.getDocument
      .fetch()
      .then(() => {
        this.title = this.$resources.getDocument.data.title;
        this.oldTitle = this.$resources.getDocument.title;
        this.content = this.$resources.getDocument.data.content;
        this.document = this.$resources.getDocument.data.document;
        this.isWriteable =
          this.$resources.getDocument.data.owner === this.userId ||
          !!this.$resources.getDocument.data.write;
        this.$store.commit("setHasWriteAccess", this.isWriteable);
        this.$resources.getDocument.data.owner =
          this.$resources.getDocument.data.owner === this.userId
            ? "Me"
            : this.$resources.getDocument.data.owner;
        this.entity = this.$resources.getDocument.data;
      })
      .then(() => {
        this.content = toUint8Array(this.$resources.getDocument.data.content);
        this.contentLoaded = true;
        let currentBreadcrumbs = [];
        currentBreadcrumbs = this.$store.state.currentBreadcrumbs;
        if (
          !currentBreadcrumbs[currentBreadcrumbs.length - 1].route.includes(
            "/document"
          )
        ) {
          currentBreadcrumbs.push({
            label: this.title,
            route: `/document/${this.entityName}`,
          });
          this.breadcrumbs = currentBreadcrumbs;
          this.$store.commit("setCurrentBreadcrumbs", currentBreadcrumbs);
        }
        this.timer = setInterval(() => {
          this.$resources.updateDocument.submit({
            entity_name: this.entityName,
            doc_name: this.document,
            title: this.titleVal,
            content: fromUint8Array(this.content),
            comments: this.comments,
            file_size: fromUint8Array(this.content).length,
          });
        }, 30000);
      });
  },
  beforeUnmount() {
    clearInterval(this.timer);
    if (!this.beforeUnmountSaveDone) {
      this.saveAndRenameDocument();
    } else {
      return;
    }
  },
  resources: {
    updateDocumentTitle() {
      return {
        url: "drive.api.files.rename_doc_entity",
        debounce: 250,
        params: {
          entity_name: this.entityName,
          title: this.titleVal,
        },
        auto: false,
      };
    },
    updateDocument() {
      return {
        url: "drive.api.files.save_doc",
        debounce: 0,
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
    rename() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        onSuccess(data) {
          data.size_in_bytes = data.file_size;
          data.file_size = formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          data.owner =
            data.owner === this.$store.state.auth.user_id ? "Me" : entity.owner;
          this.$store.commit("setEntityInfo", [data]);
          this.entity = data;
        },
        onError(error) {
          if (error && error.exc_type === "FileExistsError") {
            let getNewTitle = fetch(
              window.location.origin +
                `/api/method/drive.utils.files.get_new_title?entity=${this.$store.state.entityInfo[0].title}&parent_name=${this.entity.parent_drive_entity}`
            );
            getNewTitle
              .then((res) => res.json())
              .then((data) => {
                this.$resources.rename.submit({
                  method: "rename",
                  entity_name: this.entityName,
                  new_title: data.message,
                });
              });
          }
        },
      };
    },
    getDocument() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        method: "GET",
        params: {
          entity_name: this.entityName,
        },
        onSuccess(data) {
          data.size_in_bytes = data.file_size;
          data.file_size = formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
        },
        onError(error) {
          if (error && error.exc_type === "PermissionError") {
            this.$store.commit("setError", {
              iconName: "alert-triangle",
              iconClass: "fill-amber-500 stroke-white",
              primaryMessage: "Forbidden",
              secondaryMessage: "Insufficient permissions for this resource",
            });
          }
          this.$router.replace({ name: "Error" });
        },
        auto: false,
      };
    },
    /*     Document() {
      return {
        type: "document",
        doctype: "Drive Document",
        name: this.document,
        auto: false,
        realtime: true,
        whitelistedMethods: {
          submitVote: "submit_vote",
          stopPoll: "stop_poll",
          retractVote: "retract_vote",
        },
      };
    }, */
  },
};
</script>
