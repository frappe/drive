<template>
  <Navbar />
  <div class="flex flex-col items-center gap-5 w-full py-32">
    <LucideFileUp class="text-ink-gray-7 size-10" />
    <div class="flex flex-col items-center gap-2">
      <h3 class="text-base text-ink-gray-8">
        Quickly transfer files between devices.
      </h3>
      <h3 class="text-sm text-ink-gray-5">
        Files will be deleted after the duration you choose.
      </h3>
    </div>
    <Button
      label="Transfer"
      variant="solid"
      @click="emitter.emit('uploadFile')"
    />
  </div>
</template>
<script setup>
import Navbar from "@/components/Navbar.vue"
import emitter from "@/emitter"
</script>
