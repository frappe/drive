<template>
  <Dialog v-model="openDialog" :options="{ size: 'lg' }">
    <template #body-main>
      <div class="py-5 px-4 sm:px-6">
        <div class="flex w-full justify-between gap-x-2 mb-4">
          <div class="font-semibold text-2xl flex text-nowrap overflow-hidden">
            Sharing "
            <div class="truncate max-w-[80%]">{{ entity?.title }}</div>
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
        <div class="mb-4 border-b pb-4">
          <div class="mb-2 text-ink-gray-5 font-medium text-base">
            General Access
          </div>
          <div class="flex justify-between mt-3">
            <div class="flex flex-col gap-2">
              <div class="w-fit">
                <Autocomplete
                  v-model="generalAccessLevel"
                  :options="generalOptions"
                  :hide-search="true"
                  @update:model-value="
                    (val) => updateGeneralAccess(val, generalAccessLevel)
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
                </Autocomplete>
              </div>
            </div>
            <div class="my-auto">
              <Autocomplete
                class="my-auto"
                v-if="generalAccessLevel.value !== 'restricted'"
                :options="accessOptions"
                v-model="generalAccessType"
                :hide-search="true"
                @update:model-value="
                  (val) => updateGeneralAccess(generalAccessType, val)
                "
              />
            </div>
          </div>
        </div>
        <!-- Members section -->
        <div class="text-gray-600 font-medium text-base mb-2">Members</div>
        <div class="flex gap-3">
          <div class="flex-grow">
            <Combobox multiple v-model="sharedUsers" v-slot="{ open }">
              <div
                class="flex flex-col items-start justify-start rounded-md bg-gray-100"
              >
                <div class="flex flex-wrap justify-between py-0.5 px-2 w-full">
                  <div class="w-[75%] flex flex-wrap">
                    <Button
                      v-for="(user, idx) in sharedUsers"
                      :key="user.name"
                      :label="user.email"
                      variant="outline"
                      class="shadow-sm m-0.5 h-[24px]"
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
                      class="text-base p-1 flex-shrink min-w-24 grow basis-0 border-none bg-transparent 1 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:ring-0"
                      @change="query = $event.target.value"
                      ref="queryInput"
                      autocomplete="off"
                      v-focus
                    />
                  </div>
                  <div class="w-[25%] mt-auto"></div>
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
                  class="absolute z-[4] rounded-lg bg-surface-modal text-base shadow-2xl"
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
                        as="template"
                        :value="person"
                        :disabled="person.disabled"
                        v-slot="{ selected, active }"
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
                          <div v-else class="size-4" />
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
                        </li>
                      </ComboboxOption>
                    </template>
                  </ComboboxOptions>
                </div>
              </transition>
            </Combobox>
          </div>
          <Autocomplete
            class=""
            placeholder="Access"
            v-model="shareAccess"
            :hide-search="true"
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

        <div v-if="getUsersWithAccess.data" class="mb-3">
          <div
            v-if="!getUsersWithAccess.data?.length"
            class="text-sm w-full my-4"
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
                <span class="text-gray-700 text-sm">{{
                  user.full_name ? user.user || user.email : ""
                }}</span>
              </div>
              <span
                v-if="user.user == $store.state.user.id"
                class="ml-auto mr-1 text-gray-700"
              >
                <template v-if="user.user === entity.owner"
                  >Owner (you)</template
                >
                <template v-else>You</template>
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
                <LucideDiamond class="size-3" />
              </span>
            </div>
          </div>
        </div>
        <div v-else class="flex min-h-[19.2vh] w-full">
          <LoadingIndicator class="w-7 h-auto text-gray-700 mx-auto" />
        </div>
        <div class="w-full flex items-center justify-end gap-2">
          <Button class="text-base" variant="outline" @click="getLink(entity)">
            <template #prefix>
              <LucideLink2 />
            </template>
            Copy Link
          </Button>
          <Button
            v-if="sharedUsers.length"
            label="Invite"
            @click="addShares"
            variant="solid"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed, watch, useTemplateRef, markRaw } from "vue"
import {
  Avatar,
  Dialog,
  Autocomplete,
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

import {
  getUsersWithAccess,
  updateAccess,
  allUsers,
} from "@/resources/permissions"

import {
  LucideBuilding2,
  LucideCheck,
  LucideDiamond,
  LucideLock,
  LucideGlobe2,
} from "lucide-vue-next"
import store from "@/store"

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

const accessOptions = computed(() => {
  return props.entity.write
    ? [
        { value: "reader", label: "Can view" },
        { value: "editor", label: "Can edit" },
      ]
    : [{ value: "reader", label: "Can view" }]
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
const generalOptions = [
  {
    label: "Accessible to invited members",
    value: "restricted",
    icon: markRaw(LucideLock),
  },
  {
    label: "Accessible to team only",
    value: "team",
    icon: markRaw(LucideBuilding2),
  },
  { label: "Accessible to all", value: "public", icon: markRaw(LucideGlobe2) },
]
const generalAccessLevel = ref(generalOptions[0])
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
    generalAccessLevel.value = generalOptions.find(
      (k) => k.value === translate[getGeneralAccess.params.user]
    )

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
  if (type.value !== "restricted") {
    updateAccess.submit({
      entity_name: props.entity.name,
      user: type.value === "public" ? "" : "$TEAM",
      read: 1,
      comment: 1,
      share: 1,
      write: level.value === "editor",
    })
  }
  emit("success")
}

const openDialog = computed({
  get: () => {
    return props.modelValue === "s"
  },
  set: (value) => {
    emit("update:modelValue", value || "")
  },
})

const ACCESS_LEVELS = ["read", "comment", "share", "write"]
const filteredAccess = computed(() =>
  ACCESS_LEVELS.filter((l) => props.entity[l])
)
</script>
