<template>
  <div
    class="flex flex-col items-center h-screen p-6 text-center mt-[10%] w-full"
  >
    <div class="rounded-full flex items-center justify-center">
      <LucideFileUser v-if="error.exc_type === 'PermissionError'" />
      <LucideFileQuestionMark v-else />
    </div>
    <h1 class="text-3xl font-bold text-ink-gray-8 mt-4">Uh oh!</h1>
    <p
      class="text-lg text-ink-gray-5 mt-4"
      v-html="error.messages?.join?.('\n') || error"
    />
    <div class="w-50 flex gap-8 my-12">
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
        v-if="$store.state.user.id && $store.state.user.id !== 'Guest'"
        variant="solid"
        size="md"
        @click="$router.replace({ name: 'Home' })"
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
import store from "@/store"
import router from "@/router"
import { watchEffect } from "vue"
import { LucideFileUser } from "lucide-vue-next"

const props = defineProps({ error: Object })

watchEffect(() => {
  if (
    props.error.exc_type === "PermissionError" &&
    (!store.state.user.id || store.state.user.id === "Guest")
  ) {
    router.replace({ name: "Login" })
  }
  store.commit("setBreadcrumbs", [])
})
</script>
