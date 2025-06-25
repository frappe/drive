<template>
  <Dialog
    v-model="open"
    :options="{ size: '2xl', position: 'top' }"
  >
    <template #body>
      <div class="flex px-4 py-3 gap-1 items-center border-b">
        <LucideSearch
          class="w-4 mr-1 h-auto"
          name="search"
        />
        <input
          v-model="search"
          icon-left="search"
          type="text"
          class="appearance-none forced-colors:hidden w-full border-none bg-transparent py-3 pl-11.5 pr-4.5 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:ring-0"
          placeholder="Search"
        />
      </div>
      <div
        v-if="searchResults.data?.length"
        class="flex flex-col py-4 px-2.5 overflow-y-auto overflow-x-auto max-h-[50vh]"
      >
        <span class="mb-2 pl-1 text-base text-ink-gray-5"
          >Search results for <strong>{{ search }}:</strong></span
        >
        <div
          v-for="entity in searchResults.data"
          :key="entity.name"
          class="grid grid-flow-col grid-cols-8 gap-2 w-full items-center rounded px-2 py-2 text-base cursor-pointer hover:bg-surface-gray-2"
          @click="openEntity(null, entity), (open = false)"
        >
          <div class="flex items-center gap-2 w-full col-span-6">
            <svg
              v-if="entity.is_group"
              class="size-4"
              :draggable="false"
              :style="{ fill: entity.color }"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g clip-path="url(#clip0_1942_59507)">
                <path
                  d="M7.83412 2.88462H1.5C1.22386 2.88462 1 3.10847 1 3.38462V12.5C1 13.6046 1.89543 14.5 3 14.5H13C14.1046 14.5 15 13.6046 15 12.5V2C15 1.72386 14.7761 1.5 14.5 1.5H9.94008C9.88623 1.5 9.83382 1.51739 9.79065 1.54957L8.13298 2.78547C8.04664 2.84984 7.94182 2.88462 7.83412 2.88462Z"
                />
              </g>
              <defs>
                <clipPath id="clip0_1942_59507">
                  <rect
                    width="16"
                    height="16"
                    fill="white"
                  />
                </clipPath>
              </defs>
            </svg>
            <img
              v-else
              class="size-4"
              :src="getIconUrl(entity.file_type)"
            />
            <span class="truncate">{{ entity.title }}</span>
          </div>
          <div
            class="col-span-2 grid grid-flow-col justify-start items-center truncate"
          >
            <Avatar
              :image="entity.user_image"
              :label="entity.full_name || entity.user_name"
              class="relative mr-2"
              size="xs"
            />
            <span class="text-base text-ink-gray-8">{{
              entity.full_name || entity.user_name
            }}</span>
          </div>
        </div>
      </div>
      <div
        v-if="!searchResults.data?.length"
        class="flex flex-col py-4 px-2.5"
      >
        <span
          v-if="search.length > 3"
          class="pl-2 text-base text-ink-gray-5"
        >
          No results for <strong>"{{ search }}"</strong></span
        >
        <span
          v-else
          class="pl-2 text-sm"
          >Type more...</span
        >
      </div>
      <div
        v-if="searchResults.data?.length && !search.length"
        class="flex flex-col mb-2 mt-4 first:mt-3"
      >
        <span class="mb-1 px-4.5 text-base text-ink-gray-5">Jump to</span>
        <div class="px-2.5">
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-ink-gray-7 hover:bg-surface-gray-2"
            @click="
              $router.push({ name: 'Home' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <LucideHome class="mr-2 size-4 text-ink-gray-7" />
            Home
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-ink-gray-7 hover:bg-surface-gray-2"
            @click="
              $router.push({ name: 'Recents' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <LucideClock class="mr-2 size-4 text-ink-gray-7" />
            Recents
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-ink-gray-7 hover:bg-surface-gray-2"
            @click="
              $router.push({ name: 'Favourites' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <LucideStar class="mr-2 size-4 text-ink-gray-7" />
            Favourites
          </div>
        </div>
        <span class="mt-3 mb-1 px-4.5 text-base text-ink-gray-5">Actions</span>
        <div class="px-2.5">
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-ink-gray-7 hover:bg-surface-gray-2"
            @click="
              emitter.emit('uploadFile'), emitter.emit('showSearchPopup', false)
            "
          >
            <LucideFilePlus2
              class="stroke-[1.35] mr-2 size-4 text-ink-gray-7"
            />
            Upload File
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-ink-gray-7 hover:bg-surface-gray-2"
            @click="
              emitter.emit('uploadFolder'),
                emitter.emit('showSearchPopup', false)
            "
          >
            <LucideFolderPlus
              class="stroke-[1.35] mr-2 size-4 text-ink-gray-7"
            />
            Upload Folder
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Dialog, Avatar, createResource } from "frappe-ui"
import { getIconUrl } from "@/utils/getIconUrl"
import { openEntity } from "../utils/files"
import { ref, watch } from "vue"
import { useRoute } from "vue-router"

import LucideFilePlus2 from "~icons/lucide/file-plus-2"
import LucideFolderPlus from "~icons/lucide/folder-plus"
import LucideStar from "~icons/lucide/star"

const emit = defineEmits(["openEntity", "update:open"])
const search = ref("")
const route = useRoute()

const open = defineModel()
console.log(open.value)

const searchResults = createResource({
  auto: false,
  method: "POST",
  url: "drive.api.files.search",
})

watch(search, (val) => {
  if (val.length >= 3) {
    searchResults.submit({
      query: val,
      team: route.params.team,
    })
  } else {
    searchResults.reset()
  }
})
</script>

<style scoped>
input {
  all: unset;
}
input:focus {
  all: unset;
  outline: none;
  border: none;
}
</style>
