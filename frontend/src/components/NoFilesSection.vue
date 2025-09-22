<template>
  <div
    class="flex flex-col items-center m-auto gap-4"
    style="transform: translate(0, -88.5px)"
  >
    <div class="flex flex-col items-center gap-2">
      <div v-if="icon">
        <component
          :is="icon"
          class="size-10 text-ink-gray-5"
        />
      </div>
      <p class="text-base text-ink-gray-6 font-medium">
        {{ __(title) }}
      </p>
    </div>
    <p class="text-sm text-ink-gray-5">
      {{ __(description) }}
    </p>
    <Button
      v-if="createButton && $route.name !== 'Folder'"
      class="mt-4"
      label="Get started"
      variant="solid"
      @click="() => createButton.click()"
    />
  </div>
</template>
<script setup>
defineProps({
  icon: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    default: "Nothing here",
  },
  description: {
    type: String,
    default: "",
  },
  button: {
    type: Object,
    default: "",
  },
})
const createButton = document.querySelector("#create-button")
</script>
