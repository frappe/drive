<template>
  <div
    class="flex flex-col items-center h-screen p-6 text-center mt-[10%] w-full"
  >
    <div
      class="bg-surface-red-2 text-ink-red-4 p-4 rounded-full flex items-center justify-center w-16 h-16"
    >
      <LucideAxe />
    </div>
    <h1 class="text-3xl font-bold text-ink-gray-8 mt-4">Uh oh!</h1>
    <p
      class="text-lg text-ink-gray-5 mt-2"
      v-html="error.messages?.join?.('\n') || error"
    />
    <div class="w-50 flex gap-8 my-8">
      <Button
        v-if="$router.options.history.state.back"
        variant="outline"
        size="md"
        @click="$router.go(-1)"
      >
        <div class="flex gap-2">
          <LucideArrowBigLeft class="size-4" />Go Back
        </div>
      </Button>
      <Button
        v-if="$store.state.user.id !== 'Guest'"
        variant="solid"
        size="md"
        @click="$router.replace({ path: '/' })"
      >
        <div class="flex gap-2"><LucideHome class="size-4" />Go Home</div>
      </Button>
      <Button
        v-else
        variant="solid"
        size="md"
        @click="$router.replace('/drive/login')"
      >
        <div class="flex gap-2"><LucideUser class="size-4" />Login</div>
      </Button>
    </div>
  </div>
</template>

<script setup>
import { Button } from "frappe-ui"
defineProps({ error: Object })
</script>
