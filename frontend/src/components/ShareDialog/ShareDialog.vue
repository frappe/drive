<template>
  <Dialog v-model="openDialog" :options="{ size: 'lg' }">
    <template #body-main>
      <div class="pb-6 pt-5 max-h-[85vh]">
        <div
          class="flex items-start w-full justify-between gap-x-15 mb-3 px-4 sm:px-6"
        >
          <span class="font-semibold text-2xl truncate"
            ><template v-if="!getUsersWithAccess.data?.length"
              >Sharing </template
            ><template v-else>Permissions - </template>"{{ entity?.title }}"
          </span>
          <Button
            class="ml-auto"
            variant="ghost"
            @click="$emit('update:modelValue', false)"
          >
            <FeatherIcon name="x" class="stroke-2 h-4" />
          </Button>
        </div>

        <!-- Settings -->
        <div v-if="showSettings" class="px-4 sm:px-6">
          <div class="flex flex-col space-y-4">
            <div>
              <span class="mb-0.5 block text-sm leading-4 text-gray-700"
                >Preferences</span
              >
              <!-- <Switch v-model="allowComments" label="Allow Comments" /> -->
            </div>
            <div>
              <DatePicker
                v-model="invalidAfter"
                variant="subtle"
                label="Access Until"
              ></DatePicker>
              <span
                v-if="invalidAfter"
                class="block text-xs leading-4 text-gray-700 px-0.5 py-1.5"
              >
                Selected documents will remain shared until
                {{ useDateFormat(invalidAfter, "YY-MM-DD") }}
              </span>
              <span
                v-else
                class="block text-xs leading-4 text-gray-700 px-0.5 py-1.5"
              >
                Selected documents will remain shared indefinitely
              </span>
            </div>
          </div>
        </div>

        <div v-else-if="!getUsersWithAccess.loading">
          <!-- General Access -->
          <div class="overflow-y-auto max-h-96 px-4 sm:px-6">
            <div class="mb-3 font-medium text-base">Share:</div>
            <div class="flex mt-3">
              <TextInput
                type="email"
                class="grow"
                size="sm"
                variant="subtle"
                v-model="share.name"
                placeholder="share with..."
              />
              <div class="ms-3 w-20">
                <Autocomplete
                  :options="
                    filteredAccess.map((k) => ({
                      value: k,
                      label: k[0].toUpperCase() + k.slice(1),
                    }))
                  "
                  v-model="share.access"
                  placeholder="Select people"
                  :multiple="true"
                  :hideSearch="true"
                ></Autocomplete>
              </div>
              <Button
                :disabled="
                  share.name.length === 0 ||
                  getUsersWithAccess.data
                    .map((k) => k.user)
                    .includes(share.name)
                "
                class="ms-3"
                @click="addShare"
              >
                Share
              </Button>
            </div>
            <div
              v-if="!getUsersWithAccess.loading"
              class="text-base space-y-4 mb-5 mt-3"
            >
              <div class="mt-5 text-gray-600 font-medium text-base">
                People with access:
              </div>
              <div v-if="!getUsersWithAccess.data?.length" class="ms-2">
                <em>Yet to be shared.</em>
              </div>
              <div
                v-for="(user, idx) in getUsersWithAccess.data"
                :key="user.name"
                class="flex items-center gap-x-3"
              >
                <Avatar size="lg" :label="user.user" :image="user.user_image" />

                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    user.full_name || user.user_name || user.user
                  }}</span>
                  <span class="text-gray-700 text-sm">{{
                    user.full_name ? user.user_name || user.email : ""
                  }}</span>
                </div>
                <span
                  v-if="user.user == $store.state.auth.user_id"
                  class="ml-auto flex items-center gap-1 text-gray-600"
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
          <div class="px-6 mb-3 mt-5 text-gray-600 font-medium text-base">
            General access:
          </div>
          <div
            class="grid grid-flow-col-dense grid-cols-10 items-start justify-start mb-5 px-4 sm:px-6"
          >
            <GeneralAccess
              size="lg"
              class="col-span-1 justify-self-start row-start-1 row-end-1"
              :access-type="generalAccess.access.value"
            />
            <div class="col-span-10 mb-2 flex justify-between">
              <Autocomplete
                v-model="generalAccess.access"
                :options="[
                  { label: 'Restricted', value: 'restricted' },
                  { label: 'Public', value: 'public' },
                ]"
                :hideSearch="true"
                @update:model-value="
                  (v) =>
                    v.value === 'public'
                      ? updateAccess.submit({
                          entity_name: entity.name,
                          user: '',
                          ...generalAccess.type.reduce((acc, { value }) => {
                            acc[value] = 1
                            return acc
                          }, {}),
                        })
                      : updateAccess.submit({
                          entity_name: entity.name,
                          user: '',
                          method: 'unshare',
                        })
                "
              />
              <Autocomplete
                v-if="generalAccess.access.value === 'public'"
                class="float-right"
                :options="[
                  { value: 'read', label: 'Read' },
                  { value: 'comment', label: 'Comment' },
                  { value: 'share', label: 'Share' },
                  { value: 'write', label: 'Write' },
                ]"
                v-model="generalAccess.type"
                :multiple="true"
                :hideSearch="true"
                @update:model-value="
                  updateAccess.submit({
                    entity_name: entity.name,
                    user: '',
                    ...generalAccess.type.reduce((acc, { value }) => {
                      acc[value] = 1
                      return acc
                    }, {}),
                  })
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
        <div v-else class="flex min-h-[19.2vh] w-full">
          <LoadingIndicator class="w-7 h-auto text-gray-700 mx-auto" />
        </div>
        <div
          class="w-full flex items-center justify-between mt-2 px-4 sm:px-6 gap-x-2"
        >
          <!-- <Button
            :variant="'outline'"
            :icon-left="showSettings ? 'arrow-left' : 'settings'"
            @click="showSettings = !showSettings"
          >
            {{ showSettings ? "Back" : "Settings" }}
          </Button> -->
          <Button
            v-if="!showSettings"
            class="ml-auto"
            :variant="'outline'"
            @click="getLink(entity)"
          >
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
import { ref, computed } from "vue"
import {
  Avatar,
  Dialog,
  FeatherIcon,
  TextInput,
  Autocomplete,
  DatePicker,
  LoadingIndicator,
} from "frappe-ui"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import { getLink } from "@/utils/getLink"
import GeneralAccess from "@/components/GeneralAccess.vue"
import Link from "@/components/EspressoIcons/Link.vue"
import Diamond from "@/components/EspressoIcons/Diamond.vue"
import { getUsersWithAccess, updateAccess } from "@/resources/permissions"
import { useStore } from "vuex"
const props = defineProps({ modelValue: String, entityName: String })
const emit = defineEmits(["update:modelValue", "success"])
const store = useStore()
getUsersWithAccess.fetch({ entity_name: props.entityName })

const entity = computed(() => store.state.activeEntity)
const showSettings = ref(false)
const invalidAfter = ref()
const generalAccess = ref({
  access: { value: "restricted", label: "Restricted" },
  type: [{ value: "read", label: "Read" }],
})
const share = ref({
  name: "",
  access: [
    { value: "read", label: "Read" },
    { value: "comment", label: "Comment" },
  ],
})
const openDialog = computed({
  get: () => {
    return props.modelValue === "s"
  },
  set: (value) => {
    emit("update:modelValue", value)
  },
})

const accessMessage = computed(() => {
  if (generalAccess.value.access.value === "restricted")
    return "Limited to people with access."
  let modifiers = generalAccess.value.type.map((k) => k.value)
  let modifier =
    (modifiers.length === 1
      ? modifiers[0]
      : modifiers.slice(0, -1).join(", ") +
        ` and ${modifiers[modifiers.length - 1]}`) + " this file."
  return "Anyone on this planet can " + modifier
})
function addShare() {
  let r = {
    entity_name: entity.value.name,
    user: share.value.name,
    ...share.value.access.reduce((acc, { value }) => {
      acc[value] = 1
      return acc
    }, {}),
  }
  updateAccess.submit(r)
  getUsersWithAccess.data.push(r)
  Object.assign(share, { name: "", access: [] }), getLink(entity)
}
const ACCESS_LEVELS = ["read", "comment", "share", "write"]
const filteredAccess = computed(() =>
  ACCESS_LEVELS.filter((l) => entity.value[l])
)
</script>
