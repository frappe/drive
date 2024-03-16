<template>
  <div>
    <input
      class="hidden"
      @change="fileInputPayload"
      ref="fileInput"
      type="file"
      multiple="true"
      id="my-file-input" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue";
import { v4 as uuidv4 } from "uuid";
import Uppy from "@uppy/core";
import Tus from "@uppy/tus";
import { useStore } from "vuex";
import DropTarget from "@uppy/drop-target";

const fileInput = ref(null);
const store = useStore();
const emitter = inject("emitter");

emitter.on("uploadFile", () => {
  fileInput.value.removeAttribute("webkitdirectory");
  fileInput.value.click();
});
emitter.on("uploadFolder", () => {
  fileInput.value.setAttribute("webkitdirectory", true);
  fileInput.value.click();
});

function fileInputPayload() {
  const files = Array.from(event.target.files);
  files.forEach((file) => {
    try {
      uppy.addFile({
        source: "file input",
        name: file.name,
        type: file.type,
        data: file,
      });
    } catch (err) {
      if (err.isRestriction) {
        // handle restrictions
        console.log("Restriction error:", err);
      } else {
        // handle other errors
        console.error(err);
      }
    }
  });
}

const uppy = new Uppy({
  autoProceed: true,
  showProgressDetails: true,
  debug: true,
});
uppy.use(Tus, {
  // read site config and use that size if its bigger
  chunkSize: 50 * 1024 * 1024, //50 MB
  endpoint: "/api/method/drive.api.upload.handle_tus_request",
  withCredentials: true,
  parallelUploads: 1,
  removeFingerprintOnSuccess: true,
  onProgress: (progress) => {
    console.log("tus-js-client:", progress);
  },
  headers: {
    "X-Frappe-CSRF-Token": window.csrf_token,
    "X-Request-ID": uuidv4(),
    "Content-Type": "application/offset+octet-stream",
  },
});

uppy.use(DropTarget, {
  target: document.body,
});
uppy.on("file-added", (file) => {
  uppy.setFileMeta(file.id, {
    fileId: file.id,
  });
  store.commit("pushToUploads", {
    uuid: file.id,
    name: file.name,
    progress: 0,
  });
});

uppy.on("upload-error", (file, error, response) => {
  console.log(error);
});

uppy.on("upload-retry", (fileID) => {
  console.log("upload retried:", fileID);
});

uppy.on("upload", (data) => {
  console.log(data);
  //store.commit("updateUpload", {
  //  uuid: file.id,
  //  progress: file.progress.percentage,
  //});
});

uppy.on("upload-progress", (file, progress) => {
  console.log(file.progress.percentage);
  store.commit("updateUpload", {
    uuid: file.id,
    progress: file.progress.percentage,
  });
});

uppy.on("upload-success", (file, response) => {
  store.commit("updateUpload", {
    uuid: file.id,
    completed: true,
  });
});

/* Complete batch events */
uppy.on("progress", (progress) => {
  // progress: integer (total progress percentage)
  //console.log(progress);
});

uppy.on("error", (error) => {
  console.error(error);
});

uppy.on("complete", (result) => {
  console.log("successful files:", result.successful);
  console.log("failed files:", result.failed);
});

onBeforeUnmount(() => {
  uppy.close();
});
</script>
