<template>
  <div class="text-gray-900 antialiased flex h-screen w-screen">
    <div
      class="flex flex-1 max-h-full max-w-full"
      :class="{ 'sm:bg-gray-50': $route.meta.isPublicRoute }"
    >
      <div class="flex flex-col flex-1 max-w-full h-full">
        <Navbar
          v-if="isLoggedIn"
          :mobileSidebarIsOpen="mobileSidebarIsOpen"
          @toggleMobileSidebar="mobileSidebarIsOpen = !mobileSidebarIsOpen"
        />
        <div v-if="isLoggedIn" class="flex flex-1 h-[calc(100%_-_4rem)]">
          <div class="hidden sm:flex w-64 ml-20 sm:my-8">
            <Sidebar />
          </div>
          <div class="flex-1 sm:pr-20 sm:my-8 overflow-x-hidden overflow-y-auto">
            <router-view />
          </div>
        </div>
        <router-view v-else />
      </div>
    </div>
    <!-- Mobile Sidebar -->
    <div v-if="mobileSidebarIsOpen" class="sm:hidden fixed inset-0 z-20 flex">
      <div class="w-auto bg-white flex flex-col">
        <div class="border-b h-16 px-4 flex items-center">
          <FrappeDriveLogo />
        </div>
        <div class="flex grow p-4">
          <Sidebar
            @toggleMobileSidebar="mobileSidebarIsOpen = !mobileSidebarIsOpen"
          />
        </div>
      </div>
      <div
        class="bg-black opacity-25 grow"
        @click="mobileSidebarIsOpen = !mobileSidebarIsOpen"
      ></div>
    </div>
    <!-- Mobile Sidebar -->
  </div>
</template>
<script>
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'
import FrappeDriveLogo from '@/components/FrappeDriveLogo.vue'

export default {
  name: 'App',
  components: {
    Navbar,
    Sidebar,
    FrappeDriveLogo,
  },
  data() {
    return {
      mobileSidebarIsOpen: false,
    }
  },
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
  },
}
</script>
