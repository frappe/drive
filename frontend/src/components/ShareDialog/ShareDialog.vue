<template>
  <Dialog
    v-model="open"
    :options="{ size: 'lg' }"
    @close="dialogType = ''"
  >
    <template #body-main>
      <div class="p-4 sm:px-6">
        <!-- Header -->
        <div class="flex w-full justify-between gap-x-2 mb-4">
          <div class="font-semibold text-2xl flex text-nowrap overflow-hidden">
            Sharing "
            <div class="truncate max-w-[80%]">
              {{ entity?.title }}
            </div>
            "
          </div>
          <Button
            class="ml-auto shrink-0"
            variant="ghost"
            @click="$emit('update:modelValue', false)"
          >
            <template #icon>
              <LucideX class="size-4" />
            </template>
          </Button>
        </div>
        <div v-if="!advanced">
          <!-- General section -->
          <div class="mb-4 border-b pb-4">
            <div class="mb-2 text-ink-gray-5 font-medium text-base">
              General Access
            </div>
            <div class="flex justify-between mt-3">
              <div class="flex flex-col gap-2">
                <Select
                  v-model="generalAccessLevel"
                  :options="levelOptions"
                  @update:model-value="
                    (val) => updateGeneralAccess(val, generalPerms)
                  "
                >
                  <template #prefix>
                    <component
                      :is="generalAccessLevel.icon"
                      class="mr-2 size-4 text-ink-gray-6"
                    />
                  </template>
                  <template #item-prefix="{ option }">
                    <component
                      :is="option.icon"
                      class="size-4 text-ink-gray-6"
                    />
                  </template>
                </Select>
                <TeamSelector
                  v-if="generalAccessLevel == 'team'"
                  v-model="chosenTeam"
                />
              </div>
              <Select
                v-if="generalAccessLevel !== 'restricted'"
                v-model="generalPerms"
                :options="accessOptions"
                @update:model-value="
                  (val) => updateGeneralAccess(generalAccessLevel, val)
                "
              />
            </div>
          </div>
          <!-- Members section -->
          <div class="text-ink-gray-5 font-medium text-base mb-2">
            Members
          </div>
          <div class="flex gap-3">
            <div class="flex-grow">
              <Combobox
                v-slot="{ open }"
                v-model="sharedUsers"
                multiple
              >
                <div
                  class="flex flex-col items-start justify-center rounded-md bg-surface-gray-2"
                >
                  <div class="flex flex-wrap justify-between p-1 w-full">
                    <div class="w-[75%] flex flex-wrap">
                      <Button
                        v-for="(user, idx) in sharedUsers"
                        :key="user.name"
                        :label="user.email"
                        variant="outline"
                        class="shadow-sm m-0.5 p-1"
                      >
                        <template #prefix>
                          <Avatar
                            size="sm"
                            :image="user.image"
                            :label="user.email"
                          />
                        </template>
                        <template #suffix>
                          <LucideX
                            class="h-4"
                            stroke-width="1.5"
                            @click.stop="() => sharedUsers.splice(idx, 1)"
                          />
                        </template>
                      </Button>
                      <ComboboxInput
                        ref="queryInput"
                        v-focus
                        placeholder="Add people..."
                        class="text-base px-1.5 p-1 flex-shrink min-w-24 grow basis-0 border-none bg-transparent 1 text-ink-gray-8 placeholder-ink-gray-4 focus:ring-0"
                        autocomplete="off"
                        @change="query = $event.target.value"
                      />
                    </div>
                    <div class="w-[25%] mt-auto" />
                  </div>
                </div>

                <div
                  class="absolute z-[4] rounded-lg bg-surface-modal text-base shadow-2xl"
                >
                  <ComboboxOptions
                    v-if="open && query.length"
                    class="max-h-[15rem] overflow-y-auto px-1.5 py-1.5"
                  >
                    <ComboboxOption
                      v-if="!filteredUsers.length"
                      v-slot="{ selected, active }"
                      as="template"
                      :value="baseOption"
                    >
                      <li
                        class="flex items-center justify-between rounded px-2.5 py-1.5 text-base text-ink-gray-7"
                        :class="{
                          'bg-surface-gray-3': active,
                        }"
                      >
                        <span
                          class="block truncate"
                          :class="{
                            'font-medium': selected,
                            'font-normal': !selected,
                          }"
                        >
                          {{ query }}
                        </span>
                      </li>
                    </ComboboxOption>
                    <template
                      v-for="person in filteredUsers"
                      :key="person.email"
                    >
                      <ComboboxOption
                        v-slot="{ selected, active }"
                        as="template"
                        :value="person"
                        :disabled="person.disabled"
                      >
                        <li
                          class="flex flex-1 gap-2 overflow-hidden items-center rounded px-2.5 py-1.5 text-base text-ink-gray-7"
                          :class="{
                            'bg-surface-gray-3': active,
                            'cursor-pointer': !person.disabled,
                            'opacity-50 cursor-not-allowed': person.disabled,
                          }"
                        >
                          <LucideCheck
                            v-if="selected"
                            class="size-4 text-ink-gray-7"
                          />
                          <div
                            v-else
                            class="size-4"
                          />
                          <span
                            class="block truncate"
                            :class="{
                              'font-medium': selected,
                              'font-normal': !selected,
                            }"
                          >
                            {{ person.email }}
                            <span v-if="person.full_name">({{ person.full_name }})</span>
                          </span>
                        </li>
                      </ComboboxOption>
                    </template>
                  </ComboboxOptions>
                </div>
              </Combobox>
            </div>
            <Select
              v-model="shareAccess"
              class="flex items-start w-36"
              :options="
                advancedTweak
                  ? filteredAccess.map((k) => ({
                    value: k,
                    label: k[0].toUpperCase() + k.slice(1),
                  }))
                  : accessOptions
              "
            />
          </div>

          <div
            v-if="getUsersWithAccess.data"
            class="flex flex-col gap-4 overflow-y-auto text-base max-h-80 py-4 mb-3"
          >
            <div
              v-for="(user, idx) in getUsersWithAccess.data"
              :key="user.name"
              class="flex items-center gap-x-3 pr-1"
            >
              <Avatar
                size="xl"
                :label="user.user || user.email"
                :image="user.user_image"
              />

              <div class="flex items-start flex-col gap-1">
                <span class="font-medium text-base text-ink-gray-9">{{
                  user.full_name || user.user || user.email
                }}</span>
                <span class="text-ink-gray-7 text-sm">{{
                  user.full_name ? user.user || user.email : ""
                }}</span>
              </div>
              <span
                v-if="user.user == $store.state.user.id"
                class="ml-auto mr-1 text-ink-gray-7"
              >
                <div
                  v-if="user.user === entity.owner"
                  class="flex gap-1"
                >
                  Owner (you)
                </div>
                <template v-else>You</template>
              </span>
              <AccessButton
                v-else-if="user.user !== entity.owner"
                class="text-ink-gray-7 relative flex-shrink-0 ml-auto"
                :access-obj="user"
                :access-levels="filteredAccess"
                @update-access="
                  (access) =>
                    updateAccess.submit({
                      entity_name: entity.name,
                      user: user.user,
                      ...access,
                    })
                "
                @remove-access="
                  getUsersWithAccess.data.splice(idx, 1),
                  updateAccess.submit({
                    method: 'unshare',
                    entity_name: entity.name,
                    user: user.user,
                  })
                "
              />
              <span
                v-else
                class="ml-auto flex items-center gap-1 text-ink-gray-5"
              >
                Owner
                <LucideDiamond class="size-3" />
              </span>
            </div>
          </div>
          <div
            v-else
            class="flex min-h-[19.2vh] w-full"
          >
            <LoadingIndicator class="w-7 h-auto text-ink-gray-7 mx-auto" />
          </div>
          <div class="w-full flex items-center justify-between">
            <div>
              <Button
                class="text-sm"
                variant="ghost"
                label="Advanced"
                :icon-left="h(LucideSettings, { class: 'size-4' })"
                @click="advanced = true"
              />
            </div>
            <div class="flex gap-2">
              <Button
                class="text-base"
                variant="outline"
                @click="getLink(entity)"
              >
                <template #prefix>
                  <LucideLink2 class="w-4 text-ink-gray-6" />
                </template>
                Copy Link
              </Button>
              <Button
                v-if="sharedUsers.length"
                label="Invite"
                variant="solid"
                @click="addShares"
              />
            </div>
          </div>
        </div>
        <div v-else>
          <div
            class="flex text-sm gap-1 items-center mb-3 cursor-pointer"
            label="Back"
            @click="advanced = false"
          >
            <LucideArrowLeft class="size-4" />
            Back
          </div>

          <Switch
            v-model="allowDownload"
            label="Allow download"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed, watch, useTemplateRef, markRaw, h } from "vue"
import {
  Avatar,
  Dialog,
  LoadingIndicator,
  createResource,
  Switch,
} from "frappe-ui"
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import TeamSelector from "@/components/TeamSelector.vue"
import { getLink, dynamicList } from "@/utils/files"
import Select from "@/components/Select.vue"

import {
  getUsersWithAccess,
  updateAccess,
  allUsers,
} from "@/resources/permissions"

import LucideBuilding2 from "~icons/lucide/building-2"
import LucideCheck from "~icons/lucide/check"
import LucideDiamond from "~icons/lucide/diamond"
import LucideLock from "~icons/lucide/lock"
import LucideSettings from "~icons/lucide/settings"
import LucideArrowLeft from "~icons/lucide/arrow-left"
import LucideGlobe2 from "~icons/lucide/globe-2"

import store from "@/store"

const props = defineProps({ modelValue: String, entity: Object })
const emit = defineEmits(["update:modelValue", "success"])
const dialogType = defineModel()
const open = ref(true)

// Advanced section
const advanced = ref(false)
const allowDownload = ref(props.entity.allow_download)
watch(allowDownload, (v) => {
  props.entity.allow_download = v
  createResource({
    url: "drive.api.permissions.toggle_allow_download",
    params: { entity: props.entity.name, val: v },
    auto: true,
  })
})
getUsersWithAccess.fetch({ entity: props.entity.name })
allUsers.fetch({ team: "all" })

const levelOptions = [
  {
    label: "Accessible to invited members",
    value: "restricted",
    icon: markRaw(LucideLock),
  },
  {
    label: "Accessible to a team",
    value: "team",
    icon: markRaw(LucideBuilding2),
  },
  { label: "Accessible to all", value: "public", icon: markRaw(LucideGlobe2) },
]
const accessOptions = computed(() =>
  dynamicList([
    { value: "reader", label: "Can view", icon: LucideEye },
    {
      value: "upload",
      label: "Can upload",
      cond: props.entity.is_group && props.entity.upload,
      icon: LucideUpload,
    },
    {
      value: "editor",
      label: "Can edit",
      cond: props.entity.write,
      icon: LucidePencil,
    },
  ])
)

// General access
const generalAccessLevel = ref(levelOptions[0].value)
const generalPerms = ref("reader")
const chosenTeam = ref()

const getGeneralAccess = createResource({
  url: "drive.api.permissions.get_user_access",
  makeParams: (params) => ({
    ...params,
    entity: props.entity.name,
  }),
  onSuccess: (data) => {
    if (!data || !data.read) {
      if (getGeneralAccess.params.user === "Guest")
        getGeneralAccess.fetch({ team: 1 })
      return
    }
    generalAccessLevel.value = getGeneralAccess.params.team ? "team" : "public"
    chosenTeam.value = data.team
    generalPerms.value = data.write
      ? "editor"
      : data.upload
      ? "upload"
      : "reader"
  },
})
getGeneralAccess.fetch({ user: "Guest" })
let selectingTeam = false
const updateGeneralAccess = (level, perms) => {
  if (level === "team" && !chosenTeam.value) {
    selectingTeam = true
    return
  }
  if (level !== "restricted") {
    updateAccess.submit({
      entity_name: props.entity.name,
      user: level === "public" ? "" : chosenTeam.value,
      team: level === "team",
      read: 1,
      comment: 1,
      share: 1,
      write: perms === "editor",
      upload: perms === "editor" || perms === "upload",
    })
    selectingTeam = false
  } else {
    updateAccess.submit({
      entity_name: props.entity.name,
      user: "$GENERAL",
      method: "unshare",
    })
  }
  emit("success")
}

watch(
  chosenTeam,
  (now, prev) =>
    (prev || selectingTeam) &&
    updateGeneralAccess(generalAccessLevel.value, generalPerms.value)
)

// Invite users
const sharedUsers = ref([])
watch(sharedUsers, (now, prev) => {
  queryInput.value.el.value = ""
  query.value = ""
  if (now.length > prev.length) {
    const addedUser = sharedUsers.value[sharedUsers.value.length - 1]
    if (!allUsers.data.some((k) => k.name === addedUser.name))
      allUsers.data.push(addedUser)
  }
})
const shareAccess = ref("reader")
const advancedTweak = false
const baseOption = computed(() => ({ email: query.value, name: query.value }))
const query = ref("")
const queryInput = useTemplateRef("queryInput")
const filteredUsers = computed(() => {
  const regex = new RegExp(query.value, "i")

  return allUsers.data
    .filter(
      (k) =>
        (regex.test(k.email) || regex.test(k.full_name)) &&
        store.state.user.id != k.name
    )
    .map((k) =>
      getUsersWithAccess.data.find(({ user }) => user === k.name)
        ? { ...k, disabled: true }
        : k
    )
})
function addShares() {
  // Used to enable future advanced config
  const access =
    shareAccess.value === "editor"
      ? { read: 1, comment: 1, share: 1, upload: 1, write: 1 }
      : { read: 1, comment: 1, share: 1, upload: 0, write: 0 }
  for (const user of sharedUsers.value) {
    const r = {
      entity_name: props.entity.name,
      user: user.name,
      ...access,
    }
    updateAccess.submit(r)
    getUsersWithAccess.data.push({ ...user, ...access })
  }
  sharedUsers.value = []
  emit("success")
}

// General access

const ACCESS_LEVELS = ["read", "comment", "upload", "share", "write"]
const filteredAccess = computed(() =>
  ACCESS_LEVELS.filter((l) => props.entity[l])
)
</script>
