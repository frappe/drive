<template>
  <Dialog v-model="openDialog" :options="{ size: 'lg' }">
    <template #body-main>
      <div class="py-5 px-4 sm:px-6">
        <div class="flex w-full justify-between gap-x-15 mb-4">
          <div class="font-semibold text-2xl flex text-nowrap overflow-hidden">
            Sharing "
            <div class="truncate max-w-[80%]">{{ entity?.title }}</div>
            "
          </div>
          <Button
            class="ml-auto"
            variant="ghost"
            @click="$emit('update:modelValue', false)"
          >
            <FeatherIcon name="x" class="stroke-2 h-4" />
          </Button>
        </div>
        <Combobox multiple v-model="sharedUsers" v-slot="{ open }">
          <div
            class="flex flex-col items-start justify-start rounded bg-gray-100"
          >
            <div class="flex justify-between p-1 border-b w-full">
              <Autocomplete
                class="w-fit"
                placeholder="Access"
                v-model="shareAccess"
                :hide-search="true"
                :options="
                  advancedTweak
                    ? filteredAccess.map((k) => ({
                        value: k,
                        label: k[0].toUpperCase() + k.slice(1),
                      }))
                    : [
                        { value: 'reader', label: 'Reader' },
                        { value: 'editor', label: 'Editor' },
                      ]
                "
              />
              <div>
                <DateTimePicker
                  class="bg-inherit"
                  placeholder="Valid Until"
                  :formatter="(d) => formatDate(d)"
                  v-model="invalidAfter"
                  variant="subtle"
                />
              </div>
            </div>
            <div class="flex flex-wrap gap-1 p-2 w-full">
              <Button
                v-for="(user, idx) in sharedUsers"
                :key="user.name"
                :label="user.email"
                variant="outline"
                class="shadow-sm"
              >
                <template #suffix>
                  <LucideX
                    class="h-4"
                    stroke-width="1.5"
                    @click.stop="() => sharedUsers.splice(idx, 1)"
                  />
                </template>
              </Button>
              <ComboboxInput
                placeholder="Add people..."
                class="pl-2 w-full border-none bg-transparent py-3 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:ring-0"
                @change="query = $event.target.value"
                ref="queryInput"
                autocomplete="off"
              />
            </div>
          </div>
          <transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="transform scale-95 opacity-0"
            enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-out"
            leave-from-class="transform scale-100 opacity-100"
            leave-to-class="transform scale-95 opacity-0"
          >
            <div
              class="absolute z-[4] mt-1 rounded-lg bg-surface-modal text-base shadow-2xl"
            >
              <ComboboxOptions
                v-if="open && query.length"
                class="max-h-[15rem] overflow-y-auto px-1.5 py-1.5"
              >
                <ComboboxOption
                  as="template"
                  v-if="!filteredUsers.length"
                  :value="baseOption"
                  v-slot="{ selected, active }"
                >
                  <li
                    class="flex cursor-pointer items-center justify-between rounded px-2.5 py-1.5 text-base text-ink-gray-7"
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
                <ComboboxOption
                  v-for="person in filteredUsers"
                  as="template"
                  :key="person.email"
                  :value="person"
                  v-slot="{ selected, active }"
                >
                  <li
                    class="cursor-pointer flex justify-between rounded px-2.5 py-1.5 text-base text-ink-gray-7"
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
                      {{ person.email }}
                      <span v-if="person.full_name"
                        >({{ person.full_name }})</span
                      >
                    </span>
                    <span
                      v-if="selected"
                      :class="{
                        'text-black': active,
                        'text-gray-700': !active,
                      }"
                    >
                      <LucideCheck class="size-4" aria-hidden="true" />
                    </span>
                  </li>
                </ComboboxOption>
              </ComboboxOptions>
            </div>
          </transition>
        </Combobox>
        <Button
          :disabled="!sharedUsers.length"
          label="Invite"
          @click="addShares"
          variant="solid"
          class="w-full my-2"
        />
        <div class="my-2">
          <div class="text-gray-600 font-medium text-base mb-2">
            General access:
          </div>
          <div
            class="grid grid-flow-col-dense grid-cols-10 items-start justify-start mb-5"
          >
            <GeneralAccess
              size="lg"
              class="col-span-1 justify-self-start row-start-1 row-end-1"
              :access-type="generalAccessLevel.value"
            />
            <div class="col-span-10 mb-2 flex justify-between">
              <Autocomplete
                v-model="generalAccessLevel"
                :options="[
                  { label: 'Restricted', value: 'restricted' },
                  { label: 'Team', value: 'team' },
                  { label: 'Public', value: 'public' },
                ]"
                :hide-search="true"
                @update:model-value="
                  (val) => updateGeneralAccess(val, generalAccessType)
                "
              />
              <Autocomplete
                v-if="generalAccessLevel.value !== 'restricted'"
                class="float-right"
                :options="[
                  { value: 'reader', label: 'Reader' },
                  { value: 'editor', label: 'Editor' },
                ]"
                v-model="generalAccessType"
                :hide-search="true"
                @update:model-value="
                  (val) => updateGeneralAccess(generalAccessType, val)
                "
              ></Autocomplete>
            </div>

            <span
              class="pl-0.5 text-xs text-gray-700 row-start-2 row-end-2 col-span-6 col-start-2"
            >
              {{ accessMessage }}
            </span>
          </div>
        </div>
        <div v-if="getUsersWithAccess.data" class="mt-3">
          <div class="text-gray-600 font-medium text-base">Members</div>
          <div
            v-if="!getUsersWithAccess.data?.length"
            class="text-base text-center w-full"
          >
            No shares yet.
          </div>
          <div
            v-else
            class="flex flex-col gap-4 overflow-y-scroll text-base max-h-80 py-4"
          >
            <div
              v-for="(user, idx) in getUsersWithAccess.data"
              :key="user.name"
              class="flex items-center gap-x-3"
            >
              <Avatar
                size="xl"
                :label="user.user || user.email"
                :image="user.user_image"
              />

              <div class="flex items-start flex-col gap-1">
                <span class="text-medium">{{
                  user.full_name || user.user || user.email
                }}</span>
                <span class="text-gray-700 text-sm">{{
                  user.full_name ? user.user || user.email : ""
                }}</span>
              </div>
              <span
                v-if="user.user == $store.state.user.id"
                class="ml-auto mr-1 text-gray-700"
              >
                <em>You</em>
              </span>
              <AccessButton
                v-else-if="user.user !== entity.owner"
                class="text-gray-700 relative flex-shrink-0 ml-auto"
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
                class="ml-auto flex items-center gap-1 text-gray-600"
              >
                Owner
                <Diamond class="h-3.5" />
              </span>
            </div>
          </div>
        </div>
        <div v-else class="flex min-h-[19.2vh] w-full">
          <LoadingIndicator class="w-7 h-auto text-gray-700 mx-auto" />
        </div>
        <div class="w-full flex items-center justify-between mt-2">
          <Button class="ml-auto" :variant="'outline'" @click="getLink(entity)">
            <template #prefix>
              <Link />
            </template>
            Get Link
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed, watch, useTemplateRef } from "vue"
import { formatDate } from "@/utils/format"
import {
  Avatar,
  Dialog,
  FeatherIcon,
  Autocomplete,
  DateTimePicker,
  LoadingIndicator,
  createResource,
} from "frappe-ui"
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import { getLink } from "@/utils/getLink"
import GeneralAccess from "@/components/GeneralAccess.vue"
import Link from "@/components/EspressoIcons/Link.vue"
import Diamond from "@/components/EspressoIcons/Diamond.vue"
import {
  getUsersWithAccess,
  updateAccess,
  allUsers,
} from "@/resources/permissions"

const props = defineProps({ modelValue: String, entity: Object })
const emit = defineEmits(["update:modelValue", "success"])
getUsersWithAccess.fetch({ entity: props.entity.name })

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
const shareAccess = ref({ value: "reader" })
const advancedTweak = false
const baseOption = computed(() => ({ email: query, name: query }))
const query = ref("")
const queryInput = useTemplateRef("queryInput")
const filteredUsers = computed(() => {
  const regex = new RegExp(query.value, "i")
  return allUsers.data.filter(
    (k) => regex.test(k.email) || regex.test(k.full_name)
  )
})

function addShares() {
  // Used to enable future advanced config
  const access =
    shareAccess.value.value === "editor"
      ? { read: 1, comment: 1, share: 1, write: 1 }
      : { read: 1, comment: 1, share: 1, write: 0 }
  for (let user of sharedUsers.value) {
    let r = {
      entity_name: props.entity.name,
      user: user.name,
      valid_until: invalidAfter.value,
      ...access,
    }
    updateAccess.submit(r)
    getUsersWithAccess.data.push({ ...user, ...access })
  }
  sharedUsers.value = []
  emit("success")
}
const invalidAfter = ref()

// General access
const generalAccessLevel = ref({ value: "restricted", label: "Restricted" })
const generalAccessType = ref({ value: "reader" })
const getGeneralAccess = createResource({
  url: "drive.api.permissions.get_user_access",
  makeParams: (params) => ({ ...params, entity: props.entity.name }),
  onSuccess: (data) => {
    if (!data || !data.read) {
      if (getGeneralAccess.params.user === "")
        getGeneralAccess.fetch({ user: "$TEAM" })
      return
    }
    const translate = { "": "public", $TEAM: "team" }
    generalAccessLevel.value = {
      value: translate[getGeneralAccess.params.user],
    }
    generalAccessType.value = { value: data.write ? "editor" : "reader" }
  },
})
getGeneralAccess.fetch({ user: "" })

const updateGeneralAccess = (type, level) => {
  for (let user of ["$TEAM", ""]) {
    updateAccess.submit({
      entity_name: props.entity.name,
      user,
      method: "unshare",
    })
  }
  if (level.value !== "restricted") {
    setTimeout(() => {
      updateAccess.submit({
        entity_name: props.entity.name,
        user: level.value === "public" ? "" : "$TEAM",
        read: 1,
        comment: 1,
        share: 1,
        write: type.value === "editor",
      })
      emit("success")
    }, 1000)
  }
}

const openDialog = computed({
  get: () => {
    return props.modelValue === "s"
  },
  set: (value) => {
    emit("update:modelValue", value || "")
  },
})

const accessMessage = computed(() => {
  if (generalAccessLevel.value.value === "restricted")
    return "Limited to people with access."
  const people =
    generalAccessLevel.value.value === "team"
      ? "in your team"
      : "on this planet"
  const modifier = generalAccessType.value.value === "reader" ? "read" : "edit"
  return `Anyone ${people} can ${modifier} this file.`
})

const ACCESS_LEVELS = ["read", "comment", "share", "write"]
const filteredAccess = computed(() =>
  ACCESS_LEVELS.filter((l) => props.entity[l])
)
</script>
