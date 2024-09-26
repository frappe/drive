<template>
  <div
    class="absolute inset-0 m-auto max-h-64 max-w-lg px-16 py-8 z-10 bg-white rounded-md text-neutral-100 text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center"
  >
    <FeatherIcon
      class="h-12 mb-4"
      :class="store.state.error.iconClass"
      :name="store.state.error.iconName"
    />
    <p class="text-xl mb-2 text-black font-medium">
      {{ store.state.error.primaryMessage }}
    </p>
    <p class="text-lg text-gray-700">
      {{ store.state.error.secondaryMessage }}
    </p>
    <Button
      v-if="!hideButton"
      variant="solid"
      class="px-3 mt-6"
      @click="
        router.push({
          name: 'Home',
        })
      "
    >
      <span>{{ redirText }}</span>
    </Button>
  </div>
</template>
<script setup>
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useStore } from "vuex"
import { FeatherIcon, Button } from "frappe-ui"

const store = useStore()
const router = useRouter()

const redirText = computed(() => {
  if (store.getters.isLoggedIn) {
    return "Back to Home"
  }
  return "Login"
})
</script>
