<template>
  <TransitionGroup
    v-for="(entity, i) in entities"
    :key="entity.name"
    name="fade-in"
  >
    <UseDraggable
      v-if="entity.visible !== false"
      class="fixed"
      :initial-value="{ x: width - (i + 1) * 330, y: height - 500 }"
    >
      <div
        class="w-[300px] bg-surface-white border border-outline-gray-2 rounded-xl shadow-xl p-4 backdrop-blur-md z-30"
      >
        <div class="cursor-move flex justify-between items-start gap-1 mb-4">
          <div class="flex gap-2">
            <h2 class="text-lg font-semibold text-ink-gray-8">
              {{ entity.title }}
            </h2>
          </div>
          <Button
            variant="ghost"
            @click="entity.visible = false"
            class="min-w-[28px]"
          >
            <template #icon>
              <LucideX class="size-4" />
            </template>
          </Button>
        </div>
        <ul class="space-y-3 text-sm pb-2 text-ink-gray-5">
          <li>
            <span class="inline-block w-24 text-ink-gray-5"
              >{{ __("Owner") }}:
            </span>
            <span class="col-span-1"
              ><a href="mailto:{{ entity.owner }}">{{ entity.owner }}</a>
            </span>
          </li>

          <li>
            <span class="inline-block w-24">{{ __("Type") }}:</span>
            <span class="col-span-1">{{__(`${entity.file_type}`) }}</span>
          </li>
          <li v-if="entity.file_size">
            <span class="inline-block w-24">{{ __("Size") }}:</span>
            <span class="col-span-1">
              {{ entity.file_size_pretty }}{{ ` (${entity.file_size})` }}</span
            >
          </li>
          <li>
            <span class="inline-block w-24">{{ __("Modified") }}:</span>
            <span class="col-span-1">{{ formatDate(entity.modified) }}</span>
          </li>
          <li>
            <span class="inline-block w-24">{{ __("Added") }}:</span>
            <span class="col-span-1">{{ formatDate(entity.creation) }}</span>
          </li>
          <!-- <li>
            <span class="inline-block w-24">Path:</span>
            <span class="col-span-1">{{ entity.path }}</span>
          </li> -->
        </ul>
        <div class="flex justify-between">
          <span class="text-base font-semibold mt-2">{{ __("Access") }} </span>
          <Button
            v-if="entity.share"
            :variant="'subtle'"
            size="sm"
            class="rounded flex justify-center items-center scale-[90%]"
            @click="emitter.emit('showShareDialog')"
          >
            {{ __("Manage") }}
          </Button>
        </div>

        <div
          v-if="!access[i]"
          class="text-sm text-center italic"
        >
          {{ __("Loading...") }}
        </div>
        <ul
          v-else
          class="space-y-3 text-sm py-2"
        >
          <li class="flex">
            <span class="inline-block w-24 text-ink-gray-5"
              >{{ __("General") }}:</span
            >
            <div class="col-span-1 flex gap-2">
              <GeneralAccess
                size="sm"
                class="-mr-[3px] outline outline-white"
                :access-type="
                  generalAccess?.data?.read === 1 ? 'public' : 'restricted'
                "
              />
              <span
                >{{
                  generalAccess?.data?.read === "public"
                    ? __("Public")
                    : __("Restricted")
                }}
              </span>
            </div>
          </li>
          <li>
            <span class="inline-block w-24 text-ink-gray-5"
              >{{ __("Shared") }}:</span
            >
            <span class="col-span-1">
              {{}}
              {{
                access[i].users.message.length
                  ? access[i].users.message.length + ' ' +
                    (access[i].users.message.length === 1
                      ? __("person")
                      : __("people"))
                  : "-"
              }}
              {{
                access[i].users.message.length > 0 &&
                access[i].users.message.length < 3
                  ? "(" +
                    access[i].users.message.map((k) => k.user).join(", ") +
                    ")"
                  : ""
              }}
            </span>
          </li>
        </ul>
      </div>
    </UseDraggable>
  </TransitionGroup>
</template>

<script setup>
import { formatDate } from "@/utils/format"

import { UseDraggable } from "@vueuse/components"
import { Button } from "frappe-ui"
import { computedAsync } from "@vueuse/core"

const props = defineProps({
  entities: Array,
})

function getFileTypeVi(type) {
  if (!type) return ''
  const map = {
    'pdf': 'Tệp PDF',
    'doc': 'Tài liệu Word',
    'docx': 'Tài liệu Word',
    'xls': 'Bảng tính Excel',
    'xlsx': 'Bảng tính Excel',
    'ppt': 'Bản trình chiếu PowerPoint',
    'pptx': 'Bản trình chiếu PowerPoint',
    'jpg': 'Ảnh JPG',
    'jpeg': 'Ảnh JPG',
    'png': 'Ảnh PNG',
    'gif': 'Ảnh GIF',
    'txt': 'Tệp văn bản',
    'csv': 'Tệp CSV',
    'zip': 'Tệp nén ZIP',
    'rar': 'Tệp nén RAR',
    'mp3': 'Âm thanh MP3',
    'mp4': 'Video MP4',
    'folder': 'Thư mục',
    // Thêm các loại khác nếu cần
  }
  return map[type.toLowerCase()] || type
}

const height = document.body.clientHeight
const width = document.body.clientWidth
const access = computedAsync(async () => {
  const res = []
  for (let p of props.entities) {
    const users = await fetch(
      "/api/method/drive.api.permissions.get_shared_with_list?entity=" + p.name
    )
    const general = await fetch(
      "/api/method/drive.api.permissions.get_user_access?user=Guest&entity=" +
        p.name
    )
    res.push({
      users: await users.json(),
      general: await general.json(),
    })
  }
  return res
}, [])
</script>
