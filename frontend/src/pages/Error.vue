<template>
  <div class="m-auto flex flex-col items-center">
    <div class="flex gap-6 justify-center items-center">
      <FeatherIcon class="h-14 stroke-red-500" name="alert-triangle" />
      <div>
        <p class="text-xl text-black font-medium">
          {{ store.state.error.primaryMessage }}
        </p>
        <p class="text-lg text-gray-700">
          {{ store.state.error.secondaryMessage }}
        </p>
      </div>
    </div>
    <Button
      variant="solid"
      class="w-[30%] mt-4"
      @click="
        router.push({
          name: 'Home',
        })
      ">
      Go Back
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
