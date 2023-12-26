<template>
  <div class="hidden" />
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue";
import { useStore } from "vuex";
import Dropzone from "dropzone";

const store = useStore();
let dropzone = null;
const computedFullPath = ref("");
//const emitter = getCurrentInstance().appContext.config.globalProperties.emitter
const emitter = inject("emitter");

function doesRootFolderFullPathExist(k, file_parent) {
  const url =
    window.location.origin +
    "/api/method/" +
    `drive.api.files.does_entity_exist?name=${k}&parent_entity=${file_parent}`;

  const xhr = new XMLHttpRequest();
  // third parameter false for a synchronous request
  xhr.open("GET", url, false);
  xhr.send();

  if (xhr.status === 200) {
    const json = JSON.parse(xhr.responseText);
    return json.message;
  } else {
    throw new Error(`Request failed with status ${xhr.status}`);
  }
}

function rootFolderFullPathNewName(k, file_parent) {
  const url =
    window.location.origin +
    "/api/method/" +
    `drive.utils.files.get_new_title?entity=${k}&parent_name=${file_parent}`;

  const xhr = new XMLHttpRequest();
  xhr.open("GET", url, false); // Here i am seeting third parameter as false for a synchronous request
  xhr.send();

  if (xhr.status === 200) {
    const json = JSON.parse(xhr.responseText);
    return json.message;
  } else {
    throw new Error(`Request failed with status ${xhr.status}`);
  }
}

function rootFolderFullPath(full_path) {
  let s = full_path;
  let k = s.substring(0, s.indexOf("/"));
  return k;
}

function newFullPathName(k, s, x) {
  let f = x.replace(k, s);
  return f;
}

function NonMergeMode(file) {
  let a;
  let s;
  if (file.webkitRelativePath) {
    a = file.webkitRelativePath;
  } else {
    a = file.fullPath;
  }
  let k = rootFolderFullPath(a);
  let t = doesRootFolderFullPathExist(k, file.parent);
  if (t) {
    s = rootFolderFullPathNewName(k, file.parent);
    let z = newFullPathName(k, s, a);
    file.newFullPath = z;
  } else {
    file.newFullPath = a;
    s = k;
  }
  return s;
}

onMounted(() => {
  dropzone = new Dropzone("div#dropzoneElement", {
    paramName: "file",
    parallelUploads: 1,
    autoProcessQueue: false,
    clickable: "#dropzoneElement",
    previewsContainer: "#dropzoneElement",
    uploadMultiple: false,
    chunking: true,
    retryChunks: true,
    forceChunking: true,
    url: "/api/method/drive.api.files.upload_file",
    maxFilesize: 10 * 1024, // 10GB
    timeout: 120000, // 2 minutes
    chunkSize: 5 * 1024 * 1024, // 5MB
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      Accept: "application/json",
    },
    accept: function (file, done) {
      if (file.size == 0) {
        done("Empty files will not be uploaded.");
      } else {
        done();
      }
    },
    sending: function (file, xhr, formData) {
      if (file.lastModified) {
        formData.append("last_modified", file.lastModified);
      }
      if (file.parent) {
        formData.append("parent", file.parent);
      }
      if (file.newFullPath) {
        formData.append("fullpath", file.newFullPath);
      } else if (file.webkitRelativePath) {
        formData.append("fullpath", file.webkitRelativePath);
      } else if (file.fullPath) {
        formData.append("fullpath", file.fullPath);
      }
    },
    params: function (files, xhr, chunk) {
      if (chunk) {
        return {
          uuid: chunk.file.upload.uuid,
          chunk_index: chunk.index,
          total_file_size: chunk.file.size,
          chunk_size: dropzone.options.chunkSize,
          total_chunk_count: chunk.file.upload.totalChunkCount,
          chunk_byte_offset: chunk.index * dropzone.options.chunkSize,
        };
      }
    },
  });
  dropzone.on("addedfile", function (file) {
    file.parent = store.state.currentFolderID;
    store.commit("pushToUploads", {
      uuid: file.upload.uuid,
      name: file.name,
      progress: 0,
    });
    if (dropzone.files.length === 1) {
      if (file.fullPath || file.webkitRelativePath) {
        computedFullPath.value = NonMergeMode(file);
      }
      dropzone.options.autoProcessQueue = true;
    }
    if (file.fullPath || file.webkitRelativePath) {
      let a;
      if (file.webkitRelativePath) {
        a = file.webkitRelativePath;
      } else {
        a = file.fullPath;
      }
      let k = rootFolderFullPath(a);
      file.newFullPath = newFullPathName(k, computedFullPath.value, a);
    }
  });
  dropzone.on("queuecomplete", function (file) {
    dropzone.files = [];
    computedFullPath.value = "";
    emitter.emit("fetchFolderContents");
  });

  dropzone.on("uploadprogress", function (file, progress) {
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      progress: progress,
    });
  });
  dropzone.on("error", function (file, message) {
    let error_message;
    if (message._server_messages) {
      error_message = JSON.parse(message._server_messages)
        .map((element) => JSON.parse(element).message)
        .join("\n");
    }
    error_message = message || error_message || "Upload failed";
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      error: error_message,
    });
  });
  dropzone.on("complete", function (file) {
    store.commit("updateUpload", {
      uuid: file.upload.uuid,
      completed: true,
    });
  });
  emitter.on("uploadFile", () => {
    if (dropzone.hiddenFileInput) {
      dropzone.hiddenFileInput.removeAttribute("webkitdirectory");
      dropzone.hiddenFileInput.click();
    }
  });
  emitter.on("uploadFolder", () => {
    if (dropzone.hiddenFileInput) {
      dropzone.hiddenFileInput.setAttribute("webkitdirectory", true);
      dropzone.hiddenFileInput.click();
    }
  });
});

onBeforeUnmount(() => {
  dropzone.destroy();
});
</script>
