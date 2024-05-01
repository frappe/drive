<template>
  <div
    class="relative h-full p-5 flex flex-col lg:flex-row justify-center items-center text-center bg-neutral-50 rounded-lg"
  >
    <div class="w-8 h-8 p-1.5 m-4 rounded-full bg-red-100">
      <FeatherIcon name="x" class="text-red-500" />
    </div>
    <p class="text-2xl font-semibold">
      {{ error.messages.join("\n") }}
    </p>
    <Button
      class="absolute left-0 top-0 m-4 focus:ring-0 focus:ring-offset-0 bg-gray-200 hover:bg-gray-300"
      icon="chevron-left"
      @click="$router.go(-1)"
    />
  </div>
</template>

<script>
import { FeatherIcon, Button } from "frappe-ui"
export default {
  name: "FolderContentsError",
  components: {
    FeatherIcon,
    Button,
  },
  props: {
    error: {
      type: Object,
      required: true,
    },
  },
}
</script>
