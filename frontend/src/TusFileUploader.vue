<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue"
import { v4 as uuidv4 } from "uuid"
import Uppy from "@uppy/core"
import Tus from "@uppy/tus"
import { useStore } from "vuex"
import DropTarget from "@uppy/drop-target"

const fileInput = ref(null)
const store = useStore()
const emitter = inject("emitter")

emitter.on("uploadFile", () => {
  fileInput.value.removeAttribute("webkitdirectory")
  fileInput.value.click()
})
emitter.on("uploadFolder", () => {
  fileInput.value.setAttribute("webkitdirectory", true)
  fileInput.value.click()
})

function fileInputPayload() {
  const files = Array.from(event.target.files)
  files.forEach((file) => {
    try {
      uppy.addFile({
        source: "file input",
        name: file.name,
        type: file.type,
        data: file,
      })
    } catch (err) {
      if (err.isRestriction) {
        // handle restrictions
        console.log("Restriction error:", err)
      } else {
        // handle other errors
        console.error(err)
      }
    }
  })
}

const uppy = new Uppy({
  autoProceed: true,
  showProgressDetails: true,
  debug: true,
})
uppy.use(Tus, {
  // read site config and use that size if its bigger
  chunkSize: 20 * 1024 * 1024, //20 MB
  addRequestId: true,
  endpoint: "/api/method/drive.api.upload.handle_tus_request",
  withCredentials: true,
  limit: 1,
  parallelUploads: 1,
  removeFingerprintOnSuccess: true,
  onBeforeRequest: function (req) {
    if (req._method === "HEAD") {
    }
  },
  headers: {
    "X-Frappe-CSRF-Token": window.csrf_token,
    "X-Request-ID": uuidv4(),
    "Content-Type": "application/offset+octet-stream",
  },
})

uppy.use(DropTarget, {
  target: document.body,
})
uppy.on("file-added", (file) => {
  console.log(uppy.getFile(file.id))
  console.log(uuidv4())
  uppy.setFileMeta(file.id, {
    fileId: file.id,
    fileParent: store.state.currentFolderID,
    lastModified: file.data.lastModified,
  })
  store.commit("pushToUploads", {
    uuid: file.id,
    name: file.name,
    progress: 0,
  })
})

uppy.on("restriction-failed", (file, error) => {
  // do some customized logic like showing system notice to users
})

uppy.on("upload-error", (file, error, response) => {
  console.log(error)
})

uppy.on("upload-retry", (fileID) => {
  console.log("upload retried:", fileID)
})

uppy.on("retry-all", (fileID) => {
  console.log("upload retried:", fileID)
})

uppy.on("upload-progress", (file, progress) => {
  store.commit("updateUpload", {
    uuid: file.id,
    progress: file.progress.percentage,
  })
})

uppy.on("upload-success", (file, response) => {
  store.commit("updateUpload", {
    uuid: file.id,
    completed: true,
  })
})

/* Complete batch events */
uppy.on("progress", (progress) => {
  // progress: integer (total progress percentage)
  //console.log(progress);
})

uppy.on("error", (error) => {
  console.error(error)
})

uppy.on("complete", (result) => {
  emitter.emit("fetchFolderContents")
  uppy.cancelAll()
})

onBeforeUnmount(() => {
  uppy.close()
})
</script>
