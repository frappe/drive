<template>
  <div class="flex justify-between items-center mb-4">
    <input
      v-model="title"
      :placeholder="title"
      class="basis-auto border-0 text-2xl font-normal focus:outline-0 bg-inherit" />
    <div>
      <Button v-if="isLoggedIn" @click="$router.go(-1)">Back</Button>
    </div>
  </div>
  <TextEditor
    :editable="isWriteable"
    id="editorElem"
    v-model="content"
    :fixed-menu="true" />
</template>

<script>
import { Button } from "frappe-ui";
import TextEditor from "@/components/DocEditor/TextEditor.vue";
export default {
  components: {
    TextEditor,
    Button,
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
      title: null,
      content: null,
      document: null,
      isWriteable: false,
    };
  },
  computed: {
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
    await this.$resources.updateDocumentTitle.submit();
    await this.$resources.updateDocument.submit();
  },
  resources: {
    updateDocumentTitle() {
      return {
        url: "drive.api.files.rename_doc",
        params: {
          entity_name: this.entityName,
          doc_name: this.document,
          title: this.title,
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
        params: {
          entity_name: this.entityName,
          doc_name: this.document,
          title: this.title,
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
          console.log(data);
          this.title = data.title;
          this.content = JSON.parse(data.content);
          this.document = data.document;
          this.isWriteable = !!data.write;
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
