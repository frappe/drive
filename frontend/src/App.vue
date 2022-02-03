<template>
  <div class="text-gray-900 antialiased flex h-screen overflow-hidden">
    <div
      class="flex flex-1 overflow-y-auto"
      :class="{ 'sm:bg-gray-50': $route.meta.isLoginPage }"
    >
      <div class="flex flex-col flex-1">
        <Navbar
          v-if="isLoggedIn"
          @toggleMobileSidebar="mobileSidebarIsOpen = !mobileSidebarIsOpen"
        />
        <div v-if="isLoggedIn" class="flex flex-1 sm:px-20 sm:py-8">
          <div class="hidden sm:flex w-64">
            <Sidebar />
          </div>
          <div class="flex-1">
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
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
  },
  data() {
    return {
      mobileSidebarIsOpen: false,
    }
  },
}
</script>