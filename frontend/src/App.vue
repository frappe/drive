<template>
  <!-- Main container no scroll -->
  <div
    class="flex w-screen h-screen antialiased overflow-hidden"
    @contextmenu.prevent="handleDefaultContext($event)">
    <!-- Main container with scroll -->
    <div class="h-full w-full flex flex-col">
      <div
        v-if="(isLoggedIn && !isHybridRoute) || $route.meta.documentPage"
        class="flex h-full overflow-hidden">
        <MobileSidebar v-if="isLoggedIn" v-model="showMobileSidebar" />
        <div
          v-if="showSidebar"
          class="px-2 border-r w-[220px] bg-gray-50 hidden md:py-2 md:block">
          <Sidebar />
        </div>
        <div class="h-full w-full overflow-hidden">
          <Navbar
            v-if="(isLoggedIn && !isHybridRoute) || $route.meta.documentPage"
            :mobile-sidebar-is-open="showMobileSidebar"
            @toggle-mobile-sidebar="showMobileSidebar = !showMobileSidebar" />
          <div class="flex w-full h-full overflow-hidden">
            <div class="flex w-full h-[94%] overflow-y-scroll">
              <router-view v-slot="{ Component }">
                <component :is="Component" ref="currentPage" />
              </router-view>
            </div>
            <DocInfoSidebar
              v-if="
                $store.state.entityInfo?.document && !$route.meta.documentPage
              " />
            <InfoSidebar
              v-if="
                !$store.state.entityInfo?.document && !$route.meta.documentPage
              " />
          </div>
        </div>
      </div>
      <!-- Auth -->
      <router-view v-else />
    </div>
  </div>
  <div id="dropzoneElement" class="hidden" />
  <UploadTracker v-if="showUploadTracker" />
</template>
<script>
import Dropzone from "dropzone";
import Navbar from "@/components/Navbar.vue";
import Sidebar from "@/components/Sidebar.vue";
import InfoSidebar from "@/components/InfoSidebar.vue";
import MobileSidebar from "@/components/MobileSidebar.vue";
import UploadTracker from "@/components/UploadTracker.vue";
import { Button, FeatherIcon } from "frappe-ui";
import DocInfoSidebar from "./components/DocInfoSidebar.vue";

export default {
  name: "App",
  components: {
    Navbar,
    Sidebar,
    InfoSidebar,
    MobileSidebar,
    UploadTracker,
    Button,
    FeatherIcon,
    DocInfoSidebar,
  },
  data() {
    return {
      dropzone: null,
      showMobileSidebar: false,
      computedFullPath: "",
    };
  },
  computed: {
    showSidebar() {
      return this.$route.meta.sidebar !== false;
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    isHybridRoute() {
      return this.$route.meta.isHybridRoute;
    },
    showUploadTracker() {
      return this.isLoggedIn && this.$store.state.uploads.length > 0;
    },
    showInfoSidebar() {
      return this.$store.state.showInfo && this.$store.state.entityInfo;
    },
  },
  /* watch: {
    $route() {
      this.$store.commit("setEntityInfo", null);
      this.$store.commit("setShowInfo", false);
    },
  }, */
  async mounted() {
    let componentContext = this;
    this.dropzone = new Dropzone(this.$el.parentNode, {
      paramName: "file",
      parallelUploads: 1,
      autoProcessQueue: false,
      clickable: "#dropzoneElement",
      previewsContainer: "#dropzoneElement",
      uploadMultiple: false,
      chunking: true,
      forceChunking: true,
      url: "/api/method/drive.api.files.upload_file",
      maxFilesize: 10 * 1024, // 10GB
      timeout: 10000,
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
        if (file.parent) {
          formData.append("parent", file.parent);
        }
        if (file.new_full_path) {
          formData.append("fullpath", file.new_full_path);
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
            chunk_size: this.options.chunkSize,
            total_chunk_count: chunk.file.upload.totalChunkCount,
            chunk_byte_offset: chunk.index * this.options.chunkSize,
          };
        }
      },
    });

    this.dropzone.on("addedfile", function (file) {
      file.parent = componentContext.$store.state.currentFolderID;
      componentContext.$store.commit("pushToUploads", {
        uuid: file.upload.uuid,
        name: file.name,
        progress: 0,
      });
      if (this.files.length === 1) {
        if (file.fullPath || file.webkitRelativePath) {
          componentContext.computedFullPath = non_merge_mode(file);
        }
        this.options.autoProcessQueue = true;
      }
      if (file.fullPath || file.webkitRelativePath) {
        let a;
        if (file.webkitRelativePath) {
          a = file.webkitRelativePath;
        } else {
          a = file.fullPath;
        }
        let k = root_folder_full_path(a);
        file.new_full_path = new_full_path_name(
          k,
          componentContext.computedFullPath,
          a
        );
      }
    });
    this.dropzone.on("queuecomplete", function (file) {
      this.files = [];
      componentContext.computedFullPath = "";
    });

    this.dropzone.on("uploadprogress", function (file, progress) {
      componentContext.$store.commit("updateUpload", {
        uuid: file.upload.uuid,
        progress: progress,
      });
    });
    this.dropzone.on("error", function (file, message) {
      let error_message;
      if (message._server_messages) {
        error_message = JSON.parse(message._server_messages)
          .map((element) => JSON.parse(element).message)
          .join("\n");
      }
      error_message = message || error_message || "Upload failed";
      componentContext.$store.commit("updateUpload", {
        uuid: file.upload.uuid,
        error: error_message,
      });
    });
    this.dropzone.on("complete", function (file) {
      componentContext.currentPageEmitTrigger();
      componentContext.$store.commit("updateUpload", {
        uuid: file.upload.uuid,
        completed: true,
      });
    });
    this.emitter.on("uploadFile", () => {
      if (componentContext.dropzone.hiddenFileInput) {
        componentContext.dropzone.hiddenFileInput.click();
      }
    });
    this.emitter.on("uploadFolder", () => {
      if (componentContext.dropzone.hiddenFileInput) {
        componentContext.dropzone.hiddenFileInput.setAttribute(
          "webkitdirectory",
          true
        );
        componentContext.dropzone.hiddenFileInput.click();
      }
    });
  },
  unmounted() {
    this.dropzone.destroy();
  },
  methods: {
    handleDefaultContext(event) {
      event.preventDefault();
    },
    async currentPageEmitTrigger() {
      await this.$refs.currentPage.triggerFetchFolderEmit();
    },
  },
};

function does_root_folder_full_path_exist(k, file_parent) {
  const url =
    window.location.origin +
    "/api/method/" +
    `drive.api.files.does_entity_exist?name=${k}&parent_entity=${file_parent}`;

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

function root_folder_full_path_new_name(k, file_parent) {
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

function root_folder_full_path(full_path) {
  let s = full_path;
  let k = s.substring(0, s.indexOf("/"));
  return k;
}

function new_full_path_name(k, s, x) {
  let f = x.replace(k, s);
  return f;
}

function non_merge_mode(file) {
  let a;
  let s;
  if (file.webkitRelativePath) {
    a = file.webkitRelativePath;
  } else {
    a = file.fullPath;
  }
  let k = root_folder_full_path(a);
  let t = does_root_folder_full_path_exist(k, file.parent);
  if (t) {
    s = root_folder_full_path_new_name(k, file.parent);
    let z = new_full_path_name(k, s, a);
    file.new_full_path = z;
  } else {
    file.new_full_path = a;
    s = k;
  }
  return s;
}
</script>

<style>
/* custom scrollbar */
::-webkit-scrollbar {
  width: 0.5rem;
}

::-webkit-scrollbar-track {
  background-color: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: rgb(237, 237, 237);
  border-radius: 20px;
  border: 2px solid transparent;
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #2f3237;
}
</style>
