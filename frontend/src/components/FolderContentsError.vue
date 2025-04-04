<template>
  <div class="flex flex-col items-center h-screen p-6 text-center pt-20 w-full">
    <div
      class="bg-red-100 text-red-600 p-4 rounded-full flex items-center justify-center w-16 h-16"
    >
      <LucideAxe />
    </div>
    <h1 class="text-3xl font-bold text-gray-800 mt-4">Uh oh!</h1>
    <p
      class="text-lg text-gray-600 mt-2"
      v-html="error.messages?.join?.('\n') || error"
    ></p>
    <div class="w-50 flex gap-15 my-10">
      <Button @click="$router.go(-1)" variant="subtle" size="lg"
        ><div class="flex gap-2">
          <LucideArrowBigLeft class="w-4 h-4" />Go Back
        </div>
      </Button>
      <Button @click="$router.replace({ path: '/' })" variant="solid" size="lg"
        ><div class="flex gap-2">
          <LucideHome class="w-4 h-4" />Go Home
        </div></Button
      >
    </div>
  </div>
</template>

<script setup>
import { Button } from "frappe-ui"
defineProps({ error: Object })
</script>
