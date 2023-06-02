<template v-if="contentLoaded">
  <TextEditor
    v-model="content"
    :fixed-menu="true"
    placeholder="Start typing ..."
    :editable="isWriteable"
    :entityName="entityName" />
</template>

<script>
import TextEditor from "@/components/DocEditor/TextEditor.vue";
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
  },
  async mounted() {
    await this.$resources.getDocument.fetch();
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
    this.content = JSON.parse(this.$resources.getDocument.data.content);
    this.timer = setInterval(() => {
      this.$resources.updateDocument.submit();
    }, 30000);
  },
  beforeUnmount() {
    clearInterval(this.timer);
    this.$resources.updateDocument.submit();
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
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
    updateDocument() {
      return {
        url: "drive.api.files.save_doc",
        debounce: 500,
        params: {
          entity_name: this.entityName,
          doc_name: this.document,
          title: this.titleVal,
          content: this.content,
        },
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
    getDocument() {
      return {
        url: "drive.api.permissions.get_doc_with_permissions",
        params: {
          entity_name: this.entityName,
        },
        onSuccess(data) {
          this.title = data.title;
          this.oldTitle = data.title;
          /* Assigning content here for some reason fails :/ */
          this.document = data.document;
          this.isWriteable = !!data.write;
          this.contentLoaded = true;
        },
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
  },
};
</script>
