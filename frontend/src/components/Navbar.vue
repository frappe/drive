<template>
  <nav class="bg-white shadow">
    <div
      class="mx-auto px-5 sm:px-20 z-10 h-16 flex items-center justify-between"
    >
      <router-link to="/">
        <FrappeDriveLogo class="h-5" />
      </router-link>
      <div class="flex items-center gap-4">
        <Avatar :label="fullName" />
      </div>
    </div>
  </nav>
</template>
<script>
import FrappeDriveLogo from '@/components/FrappeDriveLogo.vue'
import { Avatar } from 'frappe-ui'
export default {
  name: 'Navbar',
  components: {
    FrappeDriveLogo,
    Avatar,
  },
  computed: {
    fullName() {
      return this.$store.state.auth.user_id
    },
  },
}
</script>