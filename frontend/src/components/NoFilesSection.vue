<template>
  <div class="flex flex-col items-center m-auto gap-4" style="transform: translate(0, -88.5px)">
    <div class="flex flex-col items-center gap-2">
      <component v-if="icon" :is="icon" class="size-8 text-ink-gray-5" />
      <p class="text-base text-ink-gray-7 font-medium">
        {{ __(title) }}
      </p>
    </div>
    <p class="text-sm text-ink-gray-5">
      {{ __(description) }}
    </p>
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
    default: 'Nothing here',
  },
  description: {
    type: String,
    default: '',
  },
  button: {
    type: Object,
    required: false,
  },
})
</script>
