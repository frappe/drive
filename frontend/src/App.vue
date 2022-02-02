<template>
  <div class="text-gray-900 flex h-screen overflow-hidden">
    <div
      class="flex flex-1 overflow-y-auto"
      :class="{ 'sm:bg-gray-50': $route.meta.isLoginPage }"
    >
      <div class="flex-1">
        <Navbar v-if="isLoggedIn" />
        <router-view />
      </div>
    </div>
  </div>
</template>
<script>
import Navbar from '@/components/Navbar.vue'
export default {
  name: 'App',
  components: {
    Navbar,
  },
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
  },
}
</script>