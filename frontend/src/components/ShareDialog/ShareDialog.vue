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
        <div
          v-if="showSettings"
          class="px-4 sm:px-6"
          :style="{
            minHeight: $refs.shareMain?.clientHeight + 'px',
          }"
        >
          <div class="flex flex-col space-y-4">
            <div>
              <span class="mb-0.5 block text-sm leading-4 text-gray-700"
                >Preferences</span
              >
              <Switch v-model="allowComments" label="Allow Comments" />
              <Switch v-model="allowDownload" label="Allow Downloading" />
            </div>
            <div>
              <DatePicker
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
              </span>
            </div>
          </div>
        </div>

        <div
          v-else-if="
            !$resources.getUsersWithAccess.loading &&
            !$resources.getGroupsWithAccess.loading
          "
          ref="shareMain"
        >
          <!-- General Access -->
          <div
            class="grid grid-flow-col-dense grid-cols-10 items-start justify-start mb-8 px-4 sm:px-6"
          >
            <GeneralAccess
              size="lg"
              class="col-span-1 justify-self-start row-start-1 row-end-1"
              :general-access="generalAccess"
            />
            <Popover
              v-slot="{ open, close }"
              class="text-gray-700 relative flex-shrink-0 justify-self-start col-span-6 mb-1"
            >
              <PopoverButton
                class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-7 items-center text-base w-auto justify-between"
              >
                {{
                  generalAccess.public
                    ? "Public"
                    : generalAccess.everyone
                    ? "Organization"
                    : "Restricted"
                }}
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
                    <Check v-if="generalAccess.public" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccess(0), close()"
                  >
                    Restricted
                    <Check
                      v-if="!generalAccess.public && !generalAccess.everyone"
                      class="h-3"
                    />
                  </li></ul
              ></PopoverPanel>
            </Popover>
            <Popover
              v-if="generalAccess.public || generalAccess.everyone"
              v-slot="{ open, close }"
              class="text-gray-700 relative flex-shrink-0 col-span-3 justify-self-end row-start-1 row-end-1"
            >
              <PopoverButton
                class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-7 items-center text-base justify-self-end"
              >
                {{ generalAccess.write ? "Can Edit" : "Can View" }}
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
                    <Check
                      v-if="
                        generalAccess.read === 1 && generalAccess.write === 0
                      "
                      class="h-3"
                    />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-x-0.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="updateGeneralAccessLvl(2), close()"
                  >
                    Can Edit
                    <Check
                      v-if="
                        generalAccess.read === 1 && generalAccess.write === 1
                      "
                      class="h-3"
                    />
                  </li></ul
              ></PopoverPanel>
            </Popover>
            <span
              class="pl-0.5 text-xs text-gray-700 row-start-2 row-end-2 col-span-6 col-start-2"
            >
              {{ accessMessage }}
            </span>
          </div>

          <UserSearch
            button-variant="solid"
            class="mb-4 px-4 sm:px-6"
            :owner="$resources.getUsersWithAccess.data.owner"
            :show-access-button="true"
            :active-users="usersWithAccess"
            :active-groups="groupsWithAccess"
            @add-new-users="(data) => updateUsers(data)"
          />

          <div class="overflow-y-auto max-h-96 px-4 sm:px-6">
            <div
              v-if="!$resources.getUsersWithAccess.loading"
              class="text-base space-y-4 mb-5"
            >
              <span class="text-gray-600 font-medium text-base">Users</span>

              <!-- Owner -->
              <div class="flex items-center gap-x-3">
                <Avatar
                  size="lg"
                  :label="$resources.getUsersWithAccess.data.owner.full_name"
                  :image="$resources.getUsersWithAccess.data.owner.user_image"
                />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    $resources.getUsersWithAccess.data.owner.full_name
                  }}</span>
                  <span class="text-gray-700 text-sm">{{
                    $resources.getUsersWithAccess.data.owner.email
                  }}</span>
                </div>
                <span class="ml-auto flex items-center gap-1 text-gray-600">
                  Owner
                  <Diamond class="h-3.5" />
                </span>
              </div>

              <!-- Users -->
              <div
                v-for="(user, index) in usersWithAccess"
                :key="user.name"
                class="flex items-center gap-x-3"
              >
                <Avatar
                  size="lg"
                  :label="user.user_name"
                  :image="user.user_image"
                />

                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    user.full_name ? user.full_name : user.user_name
                  }}</span>
                  <span class="text-gray-700 text-sm">{{
                    user.full_name ? user.user_name : ""
                  }}</span>
                </div>
                <AccessButton
                  class="text-gray-700 relative flex-shrink-0 ml-auto"
                  :access-obj="user"
                  @update-access="userAccessUpdated = true"
                  @remove-access="
                    ;(userAccessUpdated = true),
                      removeUser({ ...user, user_type: 'User' }, index)
                  "
                />
              </div>
            </div>

            <!-- Groups -->
            <div
              v-if="groupsWithAccess.length"
              class="text-base space-y-4 mb-5"
            >
              <span
                v-if="groupsWithAccess.length"
                class="text-gray-600 font-medium text-base"
                >Groups</span
              >
              <div
                v-for="(group, index) in groupsWithAccess"
                :key="group.user_name"
                class="flex items-center gap-x-3"
              >
                <Avatar size="lg" :label="group.user_name" />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{ group.user_name }}</span>
                </div>
                <AccessButton
                  class="text-gray-700 relative flex-shrink-0 ml-auto"
                  :access-obj="group"
                  @update-access="userAccessUpdated = true"
                  @remove-access="
                    ;(groupAccessUpdated = true),
                      removeUser({ ...group, user_type: 'User Group' }, index)
                  "
                />
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
<script>
import { ref } from "vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import {
  Avatar,
  Dialog,
  FeatherIcon,
  Switch,
  LoadingIndicator,
} from "frappe-ui"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import { getLink } from "@/utils/getLink"
import GeneralAccess from "@/components/GeneralAccess.vue"
import UserSearch from "@/components/ShareDialog/UserSearch.vue"
import Link from "@/components/EspressoIcons/Link.vue"
import Diamond from "@/components/EspressoIcons/Diamond.vue"
import Check from "@/components/EspressoIcons/Check.vue"
import { capture } from "@/telemetry"
import DatePicker from "frappe-ui/src/components/DatePicker.vue"
import { formatDate } from "@/utils/format"
import { useDateFormat } from "@vueuse/core"

export default {
  name: "ShareDialog",
  components: {
    Dialog,
    UserSearch,
    Avatar,
    FeatherIcon,
    Popover,
    PopoverButton,
    PopoverPanel,
    Diamond,
    Check,
    GeneralAccess,
    AccessButton,
    Link,
    Switch,
    DatePicker,
    LoadingIndicator,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entityName: {
      type: String,
      required: true,
    },
  },
  emits: ["update:modelValue", "success"],
  setup() {
    const shareMain = ref(null)
    return { shareMain }
  },
  data() {
    return {
      // mock state
      generalAccess: {
        read: 1,
        write: 0,
        share: 0,
        everyone: 0,
        public: 0,
      },
      usersWithAccess: [],
      rmUsersWithAccess: [],
      groupsWithAccess: [],
      rmGroupsWithAccess: [],
      // flags
      groupAccessUpdated: false,
      userAccessUpdated: false,
      //comments, download
      metaUpdated: false,
      invalidAfter: null,
      invalidateAfterError: null,
      allowComments: true,
      allowDownload: true,
      errorMessage: "",
      entity: null,
      showSettings: false,
    }
  },
  computed: {
    accessMessage() {
      if (this.generalAccess.public) {
        return this.generalAccess.write
          ? "Everyone with a link to this file can edit"
          : "Everyone with a link to this file can view"
      }
      if (this.generalAccess.everyone) {
        return this.generalAccess.write
          ? `Members of ${this.$resources.getOrgName.data?.org_name} can edit`
          : `Members of ${this.$resources.getOrgName.data?.org_name} can view`
      } else {
        return "Only people with access can view or edit"
      }
    },
    openDialog: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
        if (!value) {
          this.errorMessage = ""
        }
      },
    },
  },
  watch: {
    invalidAfter: {
      handler(newVal) {
        const date = new Date(newVal + " UTC")
        const unix = Math.floor(date.getTime() / 1000)
        const now = Math.floor(Date.now() / 1000)
        if (unix < now) {
          this.invalidAfter = null
          this.invalidateAfterError = "Cannot select an earlier date"
        } else {
          this.invalidateAfterError = null
          this.$resources.updateInvalidAfter.submit({
            entity_name: this.entityName,
            invalidation_date: newVal,
          })
        }
      },
    },
    allowComments: {
      handler() {
        this.$resources.toggleAllowComments.submit()
      },
    },
    allowDownload: {
      handler() {
        this.$resources.toggleAllowDownload.submit()
      },
    },
  },
  beforeUnmount() {
    if (this.userAccessUpdated) {
      let updatedUsers = this.getUpdatedOrNewEntries(
        this.$resources.getUsersWithAccess.data.users,
        this.usersWithAccess
      )
      for (let i in updatedUsers) {
        this.$resources.share.submit({
          entity_name: this.entityName,
          method: "share",
          user: updatedUsers[i].user_name,
          user_type: "User",
          read: updatedUsers[i].read,
          write: updatedUsers[i].write,
          share: 0,
        })
      }
      if (this.rmUsersWithAccess.length) {
        for (let i in this.rmUsersWithAccess) {
          this.$resources.share.submit({
            entity_name: this.entityName,
            method: "unshare",
            user: this.rmUsersWithAccess[i].user_name,
            user_type: "User",
          })
        }
      }
    }
    // update groups
    if (this.groupAccessUpdated) {
      let updatedGroups = this.getUpdatedOrNewEntries(
        this.$resources.getGroupsWithAccess.data,
        this.groupsWithAccess
      )
      for (let i in updatedGroups) {
        this.$resources.share.submit({
          entity_name: this.entityName,
          method: "share",
          user: updatedGroups[i].user_name,
          user_type: "User Group",
          read: updatedGroups[i].read,
          write: updatedGroups[i].write,
          share: 0,
        })
      }
      if (this.rmGroupsWithAccess.length) {
        for (let i in this.rmGroupsWithAccess) {
          this.$resources.share.submit({
            entity_name: this.entityName,
            method: "unshare",
            user: this.rmGroupsWithAccess[i].user_name,
            user_type: "User Group",
          })
        }
      }
    }
    // Update general access
    if (
      JSON.stringify(this.$resources.getGeneralAccess.data) !==
      JSON.stringify([this.generalAccess])
    ) {
      this.$resources.updateAccess.submit({
        method: "set_general_access",
        entity_name: this.entityName,
        read: this.generalAccess.read,
        write: this.generalAccess.write,
        share_name: this.generalAccess.name,
        share: this.generalAccess.share,
        public: this.generalAccess.public,
        everyone: this.generalAccess.everyone,
      })
    }
  },
  methods: {
    formatDate,
    useDateFormat,
    getLink,
    updateGeneralAccess(access) {
      let pub = this.generalAccess["public"]
      let org = this.generalAccess["everyone"]
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
          this.generalAccess.read = 0
          this.generalAccess.write = 0
      }
      this.generalAccess.public = pub
      this.generalAccess.everyone = org
    },
    updateGeneralAccessLvl(level) {
      let read = this.generalAccess["read"]
      let write = this.generalAccess["write"]
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
      this.generalAccess.read = read
      this.generalAccess.write = write
    },
    updateUsers(data) {
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
          this.usersWithAccess.push(userInfo)
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
    },
    getUpdatedOrNewEntries(oldList, newList) {
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
    },
    removeUser(user, idx) {
      const isUser = user.user_type === "User"
      const listToUpdate = isUser ? this.usersWithAccess : this.groupsWithAccess
      const resourceKey = isUser
        ? this.$resources.getUsersWithAccess.data.users
        : this.$resources.getGroupsWithAccess.data
      const targetList = isUser
        ? this.rmUsersWithAccess
        : this.rmGroupsWithAccess
      listToUpdate.splice(idx, 1)
      const exists = resourceKey.some(
        (item) => item.user_name === user.user_name
      )
      if (exists) {
        targetList.push({
          entity_name: this.entityName,
          user_name: user.user_name,
          user_type: user.user_type,
        })
      }
    },
  },
  resources: {
    getUsersWithAccess() {
      return {
        url: "drive.api.permissions.get_shared_with_list",
        params: {
          entity_name: this.entityName,
        },
        auto: true,
        onSuccess(data) {
          for (let i in data.users) {
            data.users[i].user_type = "User"
          }
          this.usersWithAccess = JSON.parse(JSON.stringify(data.users))
        },
      }
    },
    getGroupsWithAccess() {
      return {
        url: "drive.api.permissions.get_shared_user_group_list",
        params: {
          entity_name: this.entityName,
        },
        auto: true,
        onSuccess(data) {
          for (let i in data) {
            data[i].user_type = "User Group"
          }
          this.groupsWithAccess = JSON.parse(JSON.stringify(data))
        },
      }
    },
    getGeneralAccess() {
      return {
        url: "drive.api.permissions.get_general_access",
        params: { entity_name: this.entityName },
        auto: true,
        onSuccess(data) {
          if (data) {
            this.generalAccess = JSON.parse(JSON.stringify(data[0]))
          } else {
            this.$resources.getGeneralAccess.setData({
              read: 1,
              write: 0,
              share: 0,
              everyone: 0,
              public: 0,
            })
          }
        },
      }
    },
    entity() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        params: {
          entity_name: this.entityName,
          fields: "title,is_group,allow_comments,allow_download,owner",
        },
        onSuccess(data) {
          this.entity = data
          if (data.valid_until) {
            this.invalidAfter = data.valid_until
          }
          this.allowComments = !!data.allow_comments
          this.allowDownload = !!data.allow_download
        },
        auto: true,
      }
    },
    share() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          method: "share",
          entity_name: this.entityName,
        },
        onSuccess() {
          this.$resources.share.error = null
          capture("sharing_status_updated")
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
      }
    },
    toggleAllowComments() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          entity_name: this.entityName,
          method: "toggle_allow_comments",
          new_value: !this.allowComments,
        },
        onSuccess() {
          this.$emit("success")
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
    updateInvalidAfter() {
      return {
        url: "drive.api.permissions.update_document_invalidation",
        debounce: 500,
        params: {
          entity_name: this.entityName,
          invalidation_date: this.invalidAfter,
        },
        onSuccess() {
          this.$emit("success")
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
    toggleAllowDownload() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          entity_name: this.entityName,
          method: "toggle_allow_download",
          new_value: !this.allowDownload,
        },
        onSuccess() {
          this.$emit("success")
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
    updateAccess() {
      return {
        url: "drive.api.files.call_controller_method",
        onSuccess() {
          capture("sharing_status_updated")
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
    getOrgName() {
      return {
        url: "frappe.client.get",
        method: "GET",
        cache: "org_info",
        params: {
          doctype: "Drive Instance Settings",
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
        auto: true,
      }
    },
  },
}
</script>
