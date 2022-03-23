<template>
  <div class="flex h-screen w-screen text-gray-900 antialiased">
    <div
      class="h-full max-h-full w-full max-w-full flex-col"
      :class="{ 'sm:bg-gray-50': $route.meta.isPublicRoute }"
    >
      <Navbar
        v-if="isLoggedIn"
        :mobileSidebarIsOpen="showMobileSidebar"
        @toggleMobileSidebar="showMobileSidebar = !showMobileSidebar"
      />
      <div v-if="isLoggedIn" class="flex h-[calc(100%_-_4rem)]">
        <MobileSidebar v-model="showMobileSidebar" />
        <div class="ml-20 hidden w-64 md:my-8 md:block"><Sidebar /></div>
        <div class="flex-1 overflow-y-auto overflow-x-hidden md:my-8 md:pr-20">
          <router-view />
        </div>
      </div>
      <router-view v-else />
    </div>
    <UploadTracker v-if="showUploadTracker" />
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
