<template>
  <!-- Main container no scroll -->
  <div
    class="flex w-screen h-screen antialiased overflow-hidden"
    @contextmenu="handleDefaultContext($event)">
    <!-- Main container with scroll -->
    <div class="h-full w-full flex flex-col">
      <div
        v-if="isLoggedIn || $route.meta.isHybridRoute"
        class="flex h-full overflow-hidden">
        <Sidebar v-if="isLoggedIn" />
        <div class="h-full w-full overflow-hidden" id="dropzoneElement">
          <Navbar
            :mobile-sidebar-is-open="showMobileSidebar"
            @toggle-mobile-sidebar="showMobileSidebar = !showMobileSidebar" />
          <div class="flex w-full h-full overflow-hidden">
            <!-- Find a better way to handle the height overflow here (52px is the Navbar) -->
            <div
              class="flex w-full h-[calc(100vh-52px)]"
              :class="
                $route.meta.documentPage || $route.meta.filePage
                  ? ' overflow-y-hidden'
                  : 'overflow-y-scroll'
              ">
              <router-view v-slot="{ Component }">
                <component id="currentPage" :is="Component" ref="currentPage" />
              </router-view>
            </div>
            <InfoSidebar v-if="!$route.meta.documentPage" />
          </div>
        </div>
      </div>
      <!-- Auth -->
      <router-view v-else />
    </div>
  </div>
  <FileUploader v-if="!$route.meta.documentPage && isLoggedIn" />
  <Transition
    enter-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    enter-from-class="translate-y-1 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-1 opacity-0">
    <UploadTracker v-if="showUploadTracker" />
  </Transition>
  <Toasts />
</template>
<script>
import Navbar from "@/components/Navbar.vue";
import Sidebar from "@/components/Sidebar.vue";
import InfoSidebar from "@/components/InfoSidebar.vue";
import MobileSidebar from "@/components/MobileSidebar.vue";
import UploadTracker from "@/components/UploadTracker.vue";
import { Button, FeatherIcon } from "frappe-ui";
import { Toasts } from "@/utils/toasts.js";
import FilePicker from "./components/FilePicker.vue";
import MoveDialog from "./components/MoveDialog.vue";
import SearchPopup from "./components/SearchPopup.vue";
import FileUploader from "./components/DocEditor/FileUploader.vue";

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
    Toasts,
    FilePicker,
    MoveDialog,
    SearchPopup,
    FileUploader,
  },
  data() {
    return {
      showMobileSidebar: false,
    };
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded;
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
  },
  methods: {
    handleDefaultContext(event) {
      return this.$route.meta.documentPage ? null : event.preventDefault();
    },
    async currentPageEmitTrigger() {
      this.emitter.emit("fetchFolderContents");
    },
  },
};
</script>

<style>
/* custom scrollbar */
::-webkit-scrollbar {
  width: 0.5rem;
  height: 0.5rem;
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
