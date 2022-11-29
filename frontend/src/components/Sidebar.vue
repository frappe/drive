<template>
  <div class="flex flex-col w-60 justify-between grow">
    <div class="text-lg">
      <router-link v-for="item in sidebarItems" :key="item.label" :to="item.route" v-slot="{ href, navigate }">
        <a :class="[
          item.highlight()
            ? 'bg-gray-100 text-gray-900'
            : 'text-gray-800 hover:bg-gray-50',
        ]" :href="href" @click="navigate && $emit('toggleMobileSidebar')"
          class="w-60 h-10 p-3 gap-3 rounded-lg focus:outline-none flex grow items-center">
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
  name: 'Sidebar',
  components: { FeatherIcon },
  emits: ['toggleMobileSidebar'],
  computed: {
    sidebarItems() {
      return [
        {
          label: 'Home',
          route: '/',
          icon: 'hard-drive',
          highlight: () => {
            return this.$route.fullPath === '/'
          },
        },
        {
          label: 'Recents',
          route: '/recent',
          icon: 'clock',
          highlight: () => {
            return this.$route.fullPath.endsWith('/recent')
          },
        },
        {
          label: 'Favourites',
          route: '/favourites',
          icon: 'star',
          highlight: () => {
            return this.$route.fullPath.endsWith('/favourites')
          },
        },
        {
          label: 'Shared With Me',
          route: '/shared',
          icon: 'share-2',
          highlight: () => {
            return this.$route.fullPath.includes('/shared')
          },
        },
        {
          label: 'Trash',
          route: '/trash',
          icon: 'trash-2',
          highlight: () => {
            return this.$route.fullPath.endsWith('/trash')
          },
        },
        {
          label: 'Workspace',
          route: '/workspace',
          icon: 'tool',
          highlight: () => {
            return this.$route.fullPath.endsWith('/workspace')
          },
        },
      ]
    },
  },
}
</script>
