<template>
  <div class="flex text-gray-900 h-screen antialiased">
    <UploadTracker v-if="showUploadTracker" />
    <div class="h-full max-h-full w-full max-w-full flex flex-col"
      :class="{ 'sm:bg-gray-50': $route.meta.isPublicRoute }">
      <Navbar v-if="isLoggedIn" :mobileSidebarIsOpen="showMobileSidebar"
        @toggleMobileSidebar="showMobileSidebar = !showMobileSidebar" />
      <div v-if="isLoggedIn" class="flex h-full">
        <MobileSidebar v-model="showMobileSidebar" />
        <div class="px-3 border-r-2 hidden md:py-6 md:block">
          <Sidebar />
        </div>
        <div class="flex-1 overflow-y-auto overflow-x-hidden md:my-6 md:px-8">
          <router-view />
        </div>
      </div>
      <router-view v-else />
    </div>
  </div>
</template>
<script>
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'
import MobileSidebar from '@/components/MobileSidebar.vue'
import UploadTracker from '@/components/UploadTracker.vue'

export default {
  name: 'App',
  components: {
    Navbar,
    Sidebar,
    MobileSidebar,
    UploadTracker,
  },
  data() {
    return {
      showMobileSidebar: false,
    }
  },
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
    showUploadTracker() {
      return this.isLoggedIn && this.$store.state.uploads.length > 0
    },
  },
}
</script>
