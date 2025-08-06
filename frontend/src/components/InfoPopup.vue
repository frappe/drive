<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
  >
    <template #body-title>
      <h3
        class="text-2xl font-semibold leading-6 text-ink-gray-9 cursor-pointer"
        @click="emitter.emit('rename')"
      >
        {{ entity.title }}
      </h3>
    </template>
    <template #body-content>
      <ul class="space-y-3 text-sm mb-4 text-ink-gray-9">
        <span class="text-base font-semibold">Information</span>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Owner") }}:</span
          >
          <span class="col-span-1">
            <a :href="`mailto:${entity.owner}`">{{ entity.owner }}</a>
          </span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Type") }}:</span
          >
          <span class="col-span-1">{{ entity.file_type }}</span>
        </li>
        <li v-if="entity.file_size">
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Size") }}:</span
          >
          <span class="col-span-1">
            {{ entity.file_size_pretty }}{{ ` (${entity.file_size})` }}
          </span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Modified") }}:</span
          >
          <span class="col-span-1">{{ formatDate(entity.modified) }}</span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Added") }}:</span
          >
          <span class="col-span-1">{{ formatDate(entity.creation) }}</span>
        </li>
        <!-- <li>
          <span class="inline-block w-24">Path:</span>
          <span class="col-span-1">{{ entity.path }}</span>
        </li> -->
      </ul>
      <ul
        v-if="editor?.storage?.characterCount"
        class="space-y-3 text-sm mb-4 text-ink-gray-9"
      >
        <span class="text-base font-semibold">{{ __("Stats") }}</span>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Words") }}:</span
          >
          <span class="col-span-1">{{
            editor.storage.characterCount.words()
          }}</span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Characters") }}:</span
          >
          <span class="col-span-1">{{
            editor.storage.characterCount.characters()
          }}</span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Reading time") }}:</span
          >
          <span class="col-span-1">
            {{ Math.ceil(editor.storage.characterCount.words() / 200) }}
            {{
              Math.ceil(editor.storage.characterCount.words() / 200) > 1
                ? "mins"
                : "min"
            }}
          </span>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Modified") }}:</span
          >
          <span class="col-span-1">{{ formatDate(entity.modified) }}</span>
        </li>
      </ul>
      <div class="flex justify-between">
        <span class="text-base font-semibold">Access</span>
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
      <LoadingIndicator
        v-if="!access"
        class="size-4 mx-auto my-1"
      />
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
              :access-type="generalAccessType(access)"
            />
            <span>
              {{
                access.general?.data?.read === "public"
                  ? "Public"
                  : "Restricted"
              }}
            </span>
          </div>
        </li>
        <li>
          <span class="inline-block w-24 text-ink-gray-5"
            >{{ __("Shared") }}:</span
          >
          <span class="col-span-1">
            {{
              access.users.message.length
                ? access.users.message.length +
                  " " +
                  (access.users.message.length === 1
                    ? __("person")
                    : __("people"))
                : "-"
            }}
            {{
              access.users.message.length > 0 && access.users.message.length < 3
                ? "(" + access.users.message.map((k) => k.user).join(", ") + ")"
                : ""
            }}
          </span>
        </li>
      </ul>
    </template>
  </Dialog>
</template>

<script setup>
import { formatDate } from "@/utils/format"
import { Dialog, Button, LoadingIndicator } from "frappe-ui"
import { computedAsync } from "@vueuse/core"
import { ref, inject, watch } from "vue"
import emitter from "@/emitter"

const dialogType = defineModel()
const open = ref(true)

const editor = inject("editor")
watch(
  editor,
  () => {
    window.editor = editor?.value
  },
  { immediate: true }
)
const props = defineProps({
  entity: Object,
})

const access = computedAsync(async () => {
  const users = await fetch(
    "/api/method/drive.api.permissions.get_shared_with_list?entity=" +
      props.entity.name
  )
  const general = await fetch(
    "/api/method/drive.api.permissions.get_user_access?user=Guest&entity=" +
      props.entity.name
  )
  return {
    users: await users.json(),
    general: await general.json(),
  }
})

function generalAccessType(item) {
  // fallback for old logic
  if (item?.general?.data?.read === 1) return "public"
  if (item?.general?.data?.read === "public") return "public"
  return "restricted"
}
</script>
