<template>
  <Dialog v-model="openDialog" :options="{ size: 'lg' }">
    <template #body-main>
      <div class="pb-6 pt-5 max-h-[85vh]">
        <div
          class="flex items-start w-full justify-between gap-x-15 mb-8 px-4 sm:px-6"
        >
          <span class="font-semibold text-2xl truncate"
            >Sharing "{{ entity?.title }}"</span
          >
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
              <!-- <Switch v-model="allowDownload" label="Allow Downloading" /> -->
            </div>
            <div>
              <!-- <DatePicker
                v-model="invalidAfter"
                variant="subtle"
                label="Access Until"
              ></DatePicker>
              <span
                v-if="invalidateAfterError"
                class="block text-xs leading-4 text-red-500 px-0.5 py-1.5"
              >
                {{ invalidateAfterError }}
              </span>
              <span
                v-else-if="invalidAfter"
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
              </span> -->
            </div>
          </div>
        </div>

        <div v-else-if="!getUsersWithAccess.loading">
          <!-- General Access -->
          <div
            class="grid grid-flow-col-dense grid-cols-10 items-start justify-start mb-8 px-4 sm:px-6"
          >
            <GeneralAccess
              size="lg"
              class="col-span-1 justify-self-start row-start-1 row-end-1"
              :general-access="access.type"
            />
            <Popover
              v-slot="{ open, close }"
              class="text-gray-700 relative flex-shrink-0 justify-self-start col-span-6 mb-1"
            >
              <PopoverButton
                class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-7 items-center text-base w-auto justify-between"
              >
                {{ access.type === "public" ? "Public" : "Restricted" }}
                <FeatherIcon
                  :class="{ '[transform:rotateX(180deg)]': open }"
                  name="chevron-down"
                  class="w-3.5"
                />
              </PopoverButton>
              <PopoverPanel
                class="z-10 bg-white p-1 shadow-2xl rounded mt-1 absolute min-w-28 w-full"
                ><ul>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccess(1), close()"
                  >
                    Organization
                    <Check v-if="generalAccess.everyone" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccess(2), close()"
                  >
                    Public
                    <Check v-if="access.type === 'public'" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccess(0), close()"
                  >
                    Restricted
                    <Check v-if="access.type !== 'public'" class="h-3" />
                  </li></ul
              ></PopoverPanel>
            </Popover>
            <Popover
              v-if="access.type === 'public'"
              v-slot="{ open, close }"
              class="text-gray-700 relative flex-shrink-0 col-span-3 justify-self-end row-start-1 row-end-1"
            >
              <PopoverButton
                class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-7 items-center text-base justify-self-end"
              >
                {{ access.write ? "Can Edit" : "Can View" }}
                <FeatherIcon
                  :class="{ '[transform:rotateX(180deg)]': open }"
                  name="chevron-down"
                  class="w-3.5"
                />
              </PopoverButton>
              <PopoverPanel
                class="z-10 bg-white p-1 shadow-2xl rounded mt-1 absolute w-full"
                ><ul>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-x-0.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccessLvl(1), close()"
                  >
                    Can View
                    <Check v-if="access.read && !access.write" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-x-0.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccessLvl(2), close()"
                  >
                    Can Edit
                    <Check v-if="access.read && access.write" class="h-3" />
                  </li></ul
              ></PopoverPanel>
            </Popover>
            <span
              class="pl-0.5 text-xs text-gray-700 row-start-2 row-end-2 col-span-6 col-start-2"
            >
              {{ accessMessage }}
            </span>
          </div>

          <div class="overflow-y-auto max-h-96 px-4 sm:px-6">
            <div
              v-if="!getUsersWithAccess.loading"
              class="text-base space-y-4 mb-5"
            >
              <span class="text-gray-600 font-medium text-base">Users</span>

              <!-- Owner -->
              <!-- <div class="flex items-center gap-x-3">
                <Avatar
                  size="lg"
                  :label="getUsersWithAccess.data.owner.full_name"
                  :image="getUsersWithAccess.data.owner.user_image"
                />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    getUsersWithAccess.data.owner.full_name
                  }}</span>
                  <span class="text-gray-700 text-sm">{{
                    getUsersWithAccess.data.owner.email
                  }}</span>
                </div>
                <span class="ml-auto flex items-center gap-1 text-gray-600">
                  Owner
                  <Diamond class="h-3.5" />
                </span>
              </div> -->

              <!-- Users -->
              <div
                v-for="(user, idx) in getUsersWithAccess.data"
                :key="user.name"
                class="flex items-center gap-x-3"
              >
                <Avatar size="lg" :label="user.user" :image="user.user_image" />

                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    user.full_name ? user.full_name : user.user_name
                  }}</span>
                  <span class="text-gray-700 text-sm">{{
                    user.full_name ? user.user_name : ""
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
                  :user-access="
                    getUsersWithAccess.data.find(
                      (u) => u.user == $store.state.auth.user_id
                    )
                  "
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
        </div>
        <div v-else class="flex min-h-[19.2vh] w-full">
          <LoadingIndicator class="w-7 h-auto text-gray-700 mx-auto" />
        </div>
        <div
          class="w-full flex items-center justify-between mt-2 px-4 sm:px-6 gap-x-2"
        >
          <Button
            v-if="!showSettings"
            :variant="'outline'"
            @click="getLink(entity)"
          >
            <template #prefix>
              <Link />
            </template>
            Get Link
          </Button>
          <Button
            class="ml-auto"
            :variant="'outline'"
            :icon-left="showSettings ? 'arrow-left' : 'settings'"
            @click="showSettings = !showSettings"
          >
            {{ showSettings ? "Back" : "Settings" }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed } from "vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import {
  Avatar,
  Dialog,
  FeatherIcon,
  Switch,
  LoadingIndicator,
  DatePicker,
} from "frappe-ui"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import { getLink } from "@/utils/getLink"
import GeneralAccess from "@/components/GeneralAccess.vue"
import UserSearch from "@/components/ShareDialog/UserSearch.vue"
import Link from "@/components/EspressoIcons/Link.vue"
import Diamond from "@/components/EspressoIcons/Diamond.vue"
import Check from "@/components/EspressoIcons/Check.vue"
import { capture } from "@/telemetry"
import { formatDate } from "@/utils/format"
import { useDateFormat } from "@vueuse/core"
import { getUsersWithAccess, updateAccess } from "@/resources/permissions"
import { useStore } from "vuex"
const props = defineProps({ modelValue: String, entityName: String })
const emit = defineEmits(["update:modelValue", "success"])
const store = useStore()
getUsersWithAccess.fetch({ entity_name: props.entityName })

const entity = computed(() => store.state.activeEntity)
const access = computed(() => ({
  read: entity.value.read,
  share: entity.value.share,
  comment: entity.value.comment,
  write: entity.value.write,
  type: entity.value.type,
}))
const showSettings = ref(false)
const usersWithAccess = ref([])
const openDialog = computed({
  get: () => {
    return props.modelValue === "s"
  },
  set: (value) => {
    emit("update:modelValue", value)
  },
})

const accessMessage = computed(() => {
  if (access.value.public) {
    return access.value.write
      ? "Everyone with a link to this file can edit"
      : "Everyone with a link to this file can view"
  }
  if (access.value.everyone) {
    return access.value.write
      ? `Members of ${this.$resources.getOrgName.data?.org_name} can edit`
      : `Members of ${this.$resources.getOrgName.data?.org_name} can view`
  } else {
    return "Only people with access can view or edit"
  }
})

function updateGeneralAccess(access) {
  let pub = access.value["public"]
  let org = access.value["everyone"]
  switch (access) {
    case 1:
      pub = 0
      org = 1
      break
    case 2:
      pub = 1
      org = 0
      break
    default:
      pub = 0
      org = 0
      access.value.read = 0
      access.value.write = 0
  }
  access.value.public = pub
  access.value.everyone = org
}
function updateGeneralAccessLvl(level) {
  let read = access.value["read"]
  let write = access.value["write"]
  switch (level) {
    case 2:
      write = 1
      read = 1
      break
    case 1:
      write = 0
      read = 1
      break
    default:
      write = 0
      read = 0
  }
  access.value.read = read
  access.value.write = write
}
function updateUsers(data) {
  const { read, write } = data.access
  const processUser = (user) => {
    const userInfo = {
      user_name: user.user_name,
      read,
      write,
      share: 0,
      user_type: user.user_type,
    }
    if (user.user_type === "User") {
      userInfo.user_image = user.user_image
      userInfo.full_name = user.full_name
      usersWithAccess.value.push(userInfo)
      this.userAccessUpdated = true
      const index = this.rmUsersWithAccess.findIndex(
        (user) => user.user_name === userInfo.user_name
      )
      if (index !== -1) {
        this.rmUsersWithAccess.splice(index, 1)
      }
    } else {
      this.groupAccessUpdated = true
      this.groupsWithAccess.push(userInfo)
      const index = this.rmGroupsWithAccess.findIndex(
        (user) => user.user_name === userInfo.user_name
      )
      if (index !== -1) {
        this.rmGroupsWithAccess.splice(index, 1)
      }
    }
  }
  data.users.forEach(processUser)
}
function getUpdatedOrNewEntries(oldList, newList) {
  const updatedOrNewEntries = []
  newList.forEach((newUser) => {
    const oldUser = oldList.find(
      (oldUser) => oldUser.user_name === newUser.user_name
    )
    if (
      !oldUser ||
      oldUser.read !== newUser.read ||
      oldUser.write !== newUser.write ||
      oldUser.share !== newUser.share ||
      oldUser.full_name !== newUser.full_name
    ) {
      updatedOrNewEntries.push(newUser)
    }
  })

  return updatedOrNewEntries
}
function removeUser(user, idx) {
  const isUser = user.user_type === "User"
  const listToUpdate = isUser ? this.usersWithAccess : this.groupsWithAccess
  const resourceKey = isUser
    ? this.$resources.getUsersWithAccess.data.users
    : this.$resources.getGroupsWithAccess.data
  const targetList = isUser ? this.rmUsersWithAccess : this.rmGroupsWithAccess
  listToUpdate.splice(idx, 1)
  const exists = resourceKey.some((item) => item.user_name === user.user_name)
  if (exists) {
    targetList.push({
      entity_name: this.entityName,
      user_name: user.user_name,
      user_type: user.user_type,
    })
  }
}
</script>
