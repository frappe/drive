<template>
  <TextEditor
    v-if="contentLoaded"
    v-model="content"
    :fixed-menu="true"
    :bubble-menu="true"
    placeholder="Start typing ..."
    :isWritable="isWriteable"
    :entityName="entityName" />
</template>

<script>
import TextEditor from "@/components/DocEditor/TextEditor.vue";
import { fromUint8Array, toUint8Array } from "js-base64";
import { toast } from "../utils/toasts";

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
  /*   watch:{
    comments: {
      handler(){
        console.log(this.$store.state.allComments)
      },
      // check if userid is available
      immediate: true,
    },
  }, */
  mounted() {
    this.emitter.on("saveDocument", () => {
      this.$resources.updateDocument.submit({
        entity_name: this.entityName,
        doc_name: this.document,
        title: this.titleVal,
        content: fromUint8Array(this.content),
        comments: this.comments,
        file_size: fromUint8Array(this.content).length,
      });
    });
    //this.$store.commit("setShowInfo", true);
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
    /* this.$store.commit("setShowInfo", false); */
    clearInterval(this.timer);
    /* this.$resources.updateDocument.submit({
      entity_name: this.entityName,
      doc_name: this.document,
      title: this.titleVal,
      content: fromUint8Array(this.content),
      comments: this.comments,
      file_size: fromUint8Array(this.content).length,
    }); */
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
        debounce: 500,
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
    getDocument() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        method: "GET",
        params: {
          entity_name: this.entityName,
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
