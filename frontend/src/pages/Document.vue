<template>
  <TextEditor
    v-model="content"
    v-model:title="title"
    :fixed-menu="true"
    placeholder="Start typing ..."
    :editable="isWriteable"
    :old-title="oldTitle"
    :entityName="entityName"
    @save-title="$resources.updateDocumentTitle.submit()" />
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
    this.entityName ? await this.$resources.getDocument.fetch() : null;
    this.timer = setInterval(() => {
      this.$resources.updateDocument.submit();
    }, 30000);
  },
  async beforeUnmount() {
    clearInterval(this.timer);
    await this.$resources.updateDocument.submit();
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
          this.content = JSON.parse(data.content);
          this.document = data.document;
          this.isWriteable = !!data.write;
        },
        onError(data) {
          console.log(data);
        },
        auto: true,
      };
    },
  },
};
</script>
