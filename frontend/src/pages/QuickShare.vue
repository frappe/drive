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
    <div
      v-if="transfers.data && transfers.data.length"
      class="w-full gap-3 grid grid-cols-1 sm:grid-cols-2 mt-6 max-w-3xl px-12"
    >
      <div
        v-for="file in transfers.data"
        :key="file.name"
        class="flex justify-between rounded border border-outline-gray-modals p-3 shadow-sm"
      >
        <div class="flex flex-col gap-2 justify-center">
          <span class="text-sm font-medium text-ink-gray-9 truncate">
            {{ file.title }}
          </span>
          <span class="text-xs text-ink-gray-5">
            {{ file.file_size_pretty }} · {{ file.relativeModified }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button
            :icon="LucideDownload"
            @click="entitiesDownload(null, [{ name: file.name }], true)"
            variant="subtle"
          />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import Navbar from "@/components/Navbar.vue"
import emitter from "@/emitter"
import { createResource } from "frappe-ui"
import { prettyData } from "@/utils/files"
import LucideDownload from "~icons/lucide/download"
import { entitiesDownload } from "@/utils/download"
import { inject } from "vue"

const transform = (data) => {
  return prettyData(
    data.map((k) => {
      const modified = new Date(new Date(k.creation).getTime() + 60 * 60 * 1000)
      return {
        ...k,
        modified: modified.toISOString(),
      }
    })
  )
}

const transfers = createResource({
  url: "drive.api.list.get_transfers",
  auto: true,
  transform,
})

const socket = inject("socket")
socket.on("transfer-add", ({ file }) => {
  // broken - security
  if (file.owner === $state.store.user.id) {
    props.getEntities.data.push(...transform([file]))
    props.getEntities.setData(props.getEntities.data)
  }
})
</script>
