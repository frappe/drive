<template>
  <div
    class="flex flex-col items-center h-screen p-6 text-center mt-[10%] w-full"
  >
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
    <div class="w-50 flex gap-10 my-8">
      <Button @click="$router.go(-1)" variant="outline" size="md"
        ><div class="flex gap-2">
          <LucideArrowBigLeft class="size-4" />Go Back
        </div>
      </Button>
      <Button @click="$router.replace({ path: '/' })" variant="solid" size="md"
        ><div class="flex gap-2">
          <LucideHome class="size-4" />Go Home
        </div></Button
      >
    </div>
  </div>
</template>

<script setup>
import { Button } from "frappe-ui"
defineProps({ error: Object })
</script>
