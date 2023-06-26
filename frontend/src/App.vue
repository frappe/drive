<template>
  <div
    class="flex text-gray-900 h-screen antialiased overflow-y-hidden"
    :class="{ 'bg-slate-50': $route.meta.documentPage }"
    @contextmenu.prevent="handleDefaultContext($event)">
    <UploadTracker v-if="showUploadTracker" />
    <div
      class="h-full max-h-full w-full max-w-full flex flex-col"
      :class="{ 'sm:bg-gray-50': $route.meta.isPublicRoute }">
      <div
        v-if="(isLoggedIn && !isHybridRoute) || $route.meta.documentPage"
        class="flex h-full overflow-x-hidden">
        <MobileSidebar v-if="isLoggedIn" v-model="showMobileSidebar" />
        <div
          v-if="showSidebar"
          class="px-2 border-r w-[240px] bg-gray-50 hidden md:py-4 md:block">
          <Sidebar />
        </div>
        <div class="flex-1 overflow-y-auto overflow-x-hidden">
          <router-view v-slot="{ Component }">
            <Navbar
              v-if="(isLoggedIn && !isHybridRoute) || $route.meta.documentPage"
              :mobile-sidebar-is-open="showMobileSidebar"
              @toggle-mobile-sidebar="showMobileSidebar = !showMobileSidebar" />
            <component :is="Component" ref="currentPage" />
          </router-view>
        </div>
        <Transition
          enter-from-class="translate-x-[150%] opacity-0"
          leave-to-class="translate-x-[150%] opacity-0"
          enter-active-class="transition duration-700"
          leave-active-class="transition duration-700">
          <div v-if="showInfoSidebar" class="border-l md:pt-6 flex">
            <InfoSidebar :entity="$store.state.entityInfo" />
          </div>
        </Transition>
      </div>
      <router-view v-else />
    </div>
  </div>
  <div id="dropzoneElement" class="hidden" />
</template>
<script>
import Dropzone from "dropzone";
import Navbar from "@/components/Navbar.vue";
import Sidebar from "@/components/Sidebar.vue";
import InfoSidebar from "@/components/InfoSidebar.vue";
import MobileSidebar from "@/components/MobileSidebar.vue";
import UploadTracker from "@/components/UploadTracker.vue";

export default {
  name: "App",
  components: {
    Navbar,
    Sidebar,
    InfoSidebar,
    MobileSidebar,
    UploadTracker,
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
  watch: {
    $route() {
      this.$store.commit("setEntityInfo", null);
      this.$store.commit("setShowInfo", false);
    },
  },
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
html {
  -webkit-user-select: none;
  /* Safari */
  -ms-user-select: none;
  /* IE 10 and IE 11 */
  user-select: none;
  /* Standard syntax */
}
</style>
