<template>
  <div
    id="fileSelection"
    class="hidden"
  />
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, inject, watch } from "vue"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import Dropzone from "dropzone"
import { storageBar } from "@/resources/files"

const store = useStore()
const route = useRoute()
const emit = defineEmits(["success"])

const dropzone = ref()
const computedFullPath = ref("")
const emitter = inject("emitter")

watch(route, (to) => {
  if (!dropzone.value) return
  if (to.name === "Document" || to.name === "File") {
    dropzone.value.removeEventListeners()
  } else {
    dropzone.value.setupEventListeners()
  }
})

function doesRootFolderFullPathExist(k, file_parent) {
  const url =
    window.location.origin +
    "/api/method/" +
    `drive.api.files.does_entity_exist?name=${k}&parent_entity=${file_parent}`

  const xhr = new XMLHttpRequest()
  // third parameter false for a synchronous request
  xhr.open("GET", url, false)
  xhr.send()

  if (xhr.status === 200) {
    const json = JSON.parse(xhr.responseText)
    return json.message
  } else {
    throw new Error(`Request failed with status ${xhr.status}`)
  }
}

function rootFolderFullPathNewName(k, file_parent) {
  const url =
    window.location.origin +
    "/api/method/" +
    `drive.api.files.get_new_title?title=${k}&parent_name=${file_parent}&folder=${true}}`

  const xhr = new XMLHttpRequest()
  xhr.open("GET", url, false) // Here i am seeting third parameter as false for a synchronous request
  xhr.send()

  if (xhr.status === 200) {
    const json = JSON.parse(xhr.responseText)
    return json.message
  } else {
    throw new Error(`Request failed with status ${xhr.status}`)
  }
}

function rootFolderFullPath(full_path) {
  let s = full_path
  let k = s.substring(0, s.indexOf("/"))
  return k
}

function newFullPathName(k, s, x) {
  let f = x.replace(k, s)
  return f
}

function NonMergeMode(file) {
  let a
  let s
  if (file.webkitRelativePath) {
    a = file.webkitRelativePath
  } else {
    a = file.fullPath
  }
  let k = rootFolderFullPath(a)
  let t = doesRootFolderFullPathExist(k, file.parent)
  if (t) {
    s = rootFolderFullPathNewName(k, file.parent)
    let z = newFullPathName(k, s, a)
    file.newFullPath = z
  } else {
    file.newFullPath = a
    s = k
  }
  return s
}
onMounted(() => {
  try {
    const existing = Dropzone.forElement("div#dropzone")

    if (existing) {
      dropzone.value = existing
      return
    }
  } catch (e) {}

  dropzone.value = new Dropzone("div#dropzone", {
    paramName: "file",
    parallelUploads: 1,
    autoProcessQueue: false,
    clickable: "#fileSelection",
    disablePreviews: true,
    addRemoveLinks: true,
    hiddenInputContainer: "#fileSelection",
    // Do we want to allow multi uploads?
    chunking: true,
    url: "/api/method/drive.api.files.upload_file",
    dictUploadCanceled: "Upload canceled by user",
    maxFilesize: 10 * 1024, // 10GB
    timeout: 120000, // 2 minutes
    chunkSize: 20 * 1024 * 1024, // 20MB
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      Accept: "application/json",
    },
    addRemoveLinks: true,
    accept: function (file, done) {
      file.team = store.state.currentFolder.team || ""
      if (file.size == 0) {
        done("Empty files will not be uploaded.")
      } else {
        done()
      }
    },
    sending: function (file, _, formData) {
      formData.append("team", file.team)
      if (file.lastModified) formData.append("last_modified", file.lastModified)
      if (file.parent) formData.append("parent", file.parent)
      const path = file.newFullPath || file.webkitRelativePath || file.fullPath
      if (path) formData.append("fullpath", path)
    },
    params: function (files, xhr, chunk) {
      if (chunk) {
        return {
          uuid: chunk.file.upload.uuid,
          chunk_index: chunk.index,
          total_file_size: chunk.file.size,
          chunk_size: dropzone.value.options.chunkSize,
          total_chunk_count: chunk.file.upload.totalChunkCount,
          chunk_byte_offset: chunk.index * dropzone.value.options.chunkSize,
        }
      }
    },
  })

  dropzone.value.on("addedfile", function (file) {
    file.parent = store.state.currentFolder.name
    store.commit("addUpload", {
      uuid: file.upload.uuid,
      name: file.name,
      progress: 0,
    })
    if (dropzone.value.files.length === 1) {
      if (file.fullPath || file.webkitRelativePath) {
        computedFullPath.value = NonMergeMode(file)
      }
      dropzone.value.options.autoProcessQueue = true
    }
    if (file.fullPath || file.webkitRelativePath) {
      let a
      if (file.webkitRelativePath) {
        a = file.webkitRelativePath
      } else {
        a = file.fullPath
      }
      let k = rootFolderFullPath(a)
      file.newFullPath = newFullPathName(k, computedFullPath.value, a)
    }
  })
  dropzone.value.on("queuecomplete", function () {
    dropzone.value.files = dropzone.value.files.filter(
      (file) => file.status === Dropzone.ERROR
    )
    if (!dropzone.value.files.length) computedFullPath.value = ""
    emitter.emit("fetchFolderContents")
  })

  dropzone.value.on("dragenter", function (e) {
    console.log()
    if (e.dataTransfer.types.includes("Files"))
      this.element.classList.add("file-drag")
  })
  dropzone.value.on("dragenter", function (e) {
    if (e.dataTransfer.types.includes("Files"))
      this.element.classList.add("file-drag")
  })
  for (let event of ["dragend", "drop", "dragleave"]) {
    dropzone.value.on(event, function () {
      this.element.classList.remove("file-drag")
    })
  }
  dropzone.value.on("uploadprogress", function (file, progress) {
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      progress: progress,
    })
  })

  dropzone.value.on("error", function (file, response) {
    let message
    if (file.status === "canceled") message = "You cancelled this upload."
    else if (typeof response === "object") {
      let messages = JSON.parse(response._server_messages || "[]")
      if (messages.length) message = JSON.parse(messages[0]).message
    }
    message = message || "Please contact support."
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      error: message,
      completed: false,
    })
  })
  // REDO COMPONENT
  dropzone.value.on("success", function (file, response) {
    emitter.emit("refresh")
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      response: response.message,
    })
    storageBar.fetch(storageBar.params)
  })
  dropzone.value.on("complete", function (file) {
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      completed: true,
    })
  })
})
emitter.on("uploadFile", () => {
  if (dropzone.value.hiddenFileInput) {
    dropzone.value.hiddenFileInput.removeAttribute("webkitdirectory")
    dropzone.value.hiddenFileInput.click()
  }
})
emitter.on("cancelUpload", (uuid) => {
  var files = dropzone.value.files
  for (var i = 0; i < files.length; i++) {
    if (files[i].upload.uuid === uuid) {
      dropzone.value.removeFile(files[i])
    }
  }
})
emitter.on("retryUpload", (uuid) => {
  const file = dropzone.value.files.find((f) => f.upload.uuid === uuid)
  console.log(dropzone.value.files, uuid)
  if (file) {
    file.status = Dropzone.ADDED
    dropzone.value.enqueueFile(file)
    dropzone.value.processFile(file)
    store.commit("updateUpload", {
      uuid,
      error: null,
      progress: 0,
      completed: false,
    })
  }
})
emitter.on("cancelAllUploads", () => {
  dropzone.value.removeAllFiles(true)
})
emitter.on("uploadFolder", () => {
  if (dropzone.value.hiddenFileInput) {
    dropzone.value.hiddenFileInput.setAttribute("webkitdirectory", true)
    dropzone.value.hiddenFileInput.click()
  }
})

onBeforeUnmount(() => {
  dropzone.value.destroy()
})
</script>
