<template>
  <nav class="bg-white shadow">
    <div
      class="mx-auto px-5 md:px-20 z-10 h-16 flex items-center justify-between"
    >
      <div class="flex items-center">
        <router-link to="/" class="hidden md:block">
          <FrappeDriveLogo class="h-5" />
        </router-link>
        <div class="flex items-center md:hidden">
          <button
            class="mr-5 inline-flex items-center justify-center text-gray-700 rounded-md focus:outline-none focus:shadow-outline-gray"
            @click="$emit('toggleMobileSidebar')"
          >
            <FeatherIcon
              v-if="!mobileSidebarIsOpen"
              name="menu"
              class="w-6 h-6"
            />
            <FeatherIcon v-else name="x" class="w-6 h-6" />
          </button>
          <router-link to="/">
            <FrappeLogo class="h-6 w-auto" />
          </router-link>
        </div>
      </div>

      <div class="flex items-center">
        <div class="relative ml-3">
          <Dropdown :items="dropdownItems" right>
            <template v-slot="{ toggleDropdown }">
              <button
                class="flex items-center max-w-xs text-sm text-white rounded-full focus:outline-none focus:shadow-solid"
                id="user-menu"
                aria-label="User menu"
                aria-haspopup="true"
                @click="toggleDropdown()"
              >
                <div class="flex items-center gap-4">
                  <Avatar :label="fullName" :imageURL="imageURL" />
                </div>
              </button>
            </template>
          </Dropdown>
        </div>
      </div>
    </div>
  </nav>
</template>
<script>
import { Avatar, Dropdown, FeatherIcon } from 'frappe-ui'
import FrappeDriveLogo from '@/components/FrappeDriveLogo.vue'
import FrappeLogo from '@/components/FrappeLogo.vue'

export default {
  name: 'Navbar',
  components: {
    FrappeDriveLogo,
    FrappeLogo,
    Avatar,
    Dropdown,
    FeatherIcon,
  },
  props: {
    mobileSidebarIsOpen: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['toggleMobileSidebar'],
  data() {
    return {
      dropdownItems: [
        {
          label: 'Logout',
          action: () => this.$store.dispatch('logout'),
        },
      ],
    }
  },
  computed: {
    fullName() {
      return this.$store.state.user.fullName
    },
    imageURL() {
      return this.$store.state.user.imageURL
    },
  },
}
</script>
