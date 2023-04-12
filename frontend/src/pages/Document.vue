<template>
  <div class="flex justify-between items-center mb-4">
    <input
      v-model="title"
      class="basis-3/4 border-0 bg-white text-3xl font-normal focus:outline-0"
      placeholder="Untitled Document" />
    <div>
      <Button
        class="flex-none mr-1"
        appearance="primary"
        @click="
          $resources.createDocument.submit({
            title: title,
            content: content,
            parent: currentFolderID,
          })
        ">
        Save
      </Button>
      <Button @click="$router.go(-1)">Discard</Button>
    </div>
  </div>
  <TextEditor
    id="editorElem"
    v-model="content"
    editor-class="border max-w-none rounded-b-lg p-3 overflow-auto focus:outline-none"
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
  data() {
    return {
      title: null,
      content: null,
    };
  },
  computed: {
    currentFolderID() {
      return this.$store.state.currentFolderID;
    },
  },
  methods: {
    test() {
      this.emitter.emit("uploadFile");
    },
  },
  resources: {
    createDocument() {
      return {
        url: "drive.api.files.create_document_entity",
        params: {
          title: this.title,
          content: this.content,
          parent: this.currentFolderID,
        },
        onSuccess(data) {
          console.log(data);
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
