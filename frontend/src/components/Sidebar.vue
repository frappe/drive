<template>
  <div class="flex flex-col w-44 justify-between grow">
    <div class="text-lg">
      <router-link
        v-for="item in sidebarItems"
        :key="item.label"
        :to="item.route"
        v-slot="{ href, navigate }"
      >
        <a
          :class="[
            item.highlight()
              ? 'bg-blue-50 text-blue-500'
              : 'text-gray-900 hover:bg-gray-50',
          ]"
          :href="href"
          @click="navigate && $emit('toggleMobileSidebar')"
          class="w-44 h-10 p-3 gap-3 rounded focus:outline-none flex grow items-center"
        >
          <FeatherIcon :name="item.icon" class="stroke-1 w-5 h-5" />
          {{ item.label }}
        </a>
      </router-link>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from 'frappe-ui'
export default {
  components: { FeatherIcon },
  name: 'Sidebar',
  computed: {
    sidebarItems() {
      return [
        {
          label: 'My Files',
          route: '/',
          icon: 'hard-drive',
          highlight: () => {
            return this.$route.fullPath.endsWith('/')
          },
        },
        {
          label: 'Recent',
          route: '/recent',
          icon: 'clock',
          highlight: () => {
            return this.$route.fullPath.endsWith('/recent')
          },
        },
        {
          label: 'Shared With Me',
          route: '/shared',
          icon: 'share-2',
          highlight: () => {
            return this.$route.fullPath.endsWith('/shared')
          },
        },
      ]
    },
  },
  data() {
    return {}
  },
}
</script>
