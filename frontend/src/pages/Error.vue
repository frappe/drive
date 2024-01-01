<template>
  <div class="m-auto flex flex-col items-center justify-center">
    <FeatherIcon
      class="h-12 mb-4"
      :class="store.state.error.iconClass"
      :name="store.state.error.iconName" />
    <p class="text-xl mb-2 text-black font-medium">
      {{ store.state.error.primaryMessage }}
    </p>
    <p class="text-lg text-gray-700">
      {{ store.state.error.secondaryMessage }}
    </p>
    <Button
      variant="solid"
      class="px-3 mt-2"
      @click="
        router.push({
          name: 'Home',
        })
      ">
      Back to Home
    </Button>
  </div>
</template>
<script setup>
import { useRouter } from "vue-router";
import { useStore } from "vuex";
import { FeatherIcon, Button } from "frappe-ui";

const store = useStore();
const router = useRouter();
</script>
