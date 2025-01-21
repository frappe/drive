<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white top-0 border-b min-w-full"
  >
    <div
      class="mx-auto pl-4 py-2.5 pr-2 h-12 z-10 flex items-center justify-between"
    >
      <Breadcrumbs />
      <div class="flex gap-1">
        <div
          v-if="connectedUsers.length > 1 && isLoggedIn"
          class="hidden sm:flex bg-gray-200 rounded justify-center items-center px-1"
        >
          <UsersBar />
        </div>
        <div v-if="isLoggedIn" class="block sm:flex">
          <Button
            v-if="
              ($route.name === 'Document' ||
                $route.name === 'File' ||
                $route.name === 'Whiteboard') &&
              $store.state.activeEntity.owner !== 'You'
            "
            :variant="'solid'"
            class="bg-gray-200 rounded flex justify-center items-center px-1"
            @click="emitter.emit('showShareDialog')"
          >
            <template #prefix>
              <Share class="w-4" />
            </template>
            Share
          </Button>
          <template v-for="button of possibleButtons" :key="button.route">
            <Button
              v-if="$route.name === button.route"
              class="line-clamp-1 truncate w-full"
              :disabled="!button.entities.data.length"
              :variant="'subtle'"
              :theme="button.theme || 'gray'"
              @click="emitter.emit('showCTADelete')"
            >
              <template #prefix>
                <FeatherIcon :name="button.icon" class="w-4" />
              </template>
              {{ button.label }}
            </Button>
          </template>
        </div>
        <div v-else class="ml-auto">
          <Button variant="solid" @click="$router.push({ name: 'Login' })">
            Sign In
          </Button>
        </div>
      </div>
    </div>
  </nav>
</template>
<script setup>
import UsersBar from "./UsersBar.vue"
import { FeatherIcon, Button } from "frappe-ui"
import Breadcrumbs from "@/components/Breadcrumbs.vue"
import Share from "./EspressoIcons/Share.vue"
import { useStore } from "vuex"
import { computed } from "vue"
import { getRecents, getFavourites, getTrash } from "@/resources/files"

const store = useStore()
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const connectedUsers = computed(() => store.state.connectedUsers)

const possibleButtons = [
  { route: "Recents", label: "Clear", icon: "clock", entities: getRecents },
  {
    route: "Favourites",
    label: "Clear",
    icon: "star",
    entities: getFavourites,
  },
  {
    route: "Trash",
    label: "Empty Trash",
    icon: "trash",
    entities: getTrash,
    theme: "red",
  },
]
</script>
