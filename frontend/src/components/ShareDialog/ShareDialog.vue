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
        <div
          v-if="showSettings"
          class="px-4 sm:px-6"
          :style="{
            minHeight: $refs.shareMain?.clientHeight + 'px',
          }"
        >
          <span class="text-gray-600 font-medium text-base">Settings</span>
          <div class="flex flex-col space-y-0 mt-4">
            <Switch v-model="allowComments" label="Allow Comments" />
            <Switch v-model="allowDownload" label="Allow Downloading" />
          </div>
        </div>
        <div
          v-else-if="
            !$resources.sharedWith.loading &&
            !$resources.sharedWithUserGroup.loading
          "
          ref="shareMain"
        >
          <div
            class="grid grid-flow-col-dense grid-cols-10 items-start justify-start mb-8 px-4 sm:px-6"
          >
            <GeneralAccess
              size="xl"
              class="col-span-1 justify-self-start row-start-1 row-end-1"
              :general-access="generalAccess"
            />
            <Popover
              v-slot="{ open, close }"
              class="text-gray-700 relative flex-shrink-0 justify-self-start col-span-6"
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
                  class="w-4"
                />
              </PopoverButton>
              <PopoverPanel
                class="z-10 bg-white p-1 shadow-2xl rounded mt-1 absolute min-w-28 w-full"
                ><ul>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="
                      ;(generalAccess.public = 0),
                        (generalAccess.everyone = 1),
                        close()
                    "
                  >
                    Organization
                    <Check v-if="generalAccess.everyone" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="
                      ;(generalAccess.public = 1),
                        (generalAccess.everyone = 0),
                        close()
                    "
                  >
                    Public
                    <Check v-if="generalAccess.public" class="h-3" />
                  </li>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="
                      ;(generalAccess.public = 0),
                        (generalAccess.read = 0),
                        (generalAccess.write = 0),
                        (generalAccess.everyone = 0),
                        close()
                    "
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
                  class="w-4"
                />
              </PopoverButton>
              <PopoverPanel
                class="z-10 bg-white p-1 shadow-2xl rounded mt-1 absolute w-full"
                ><ul>
                  <li
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="
                      generalAccess.read === 1,
                        (generalAccess.write = 0),
                        close()
                    "
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
                    class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
                    @click="
                      generalAccess.read === 1,
                        (generalAccess.write = 1),
                        close()
                    "
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
              class="text-xs text-gray-700 row-start-2 row-end-2 col-span-6 col-start-2"
            >
              {{ accessMessage }}
            </span>
          </div>
          <UserSearch
            button-variant="solid"
            class="mb-4 px-4 sm:px-6"
            :owner="$resources.sharedWith.data.owner"
            :active-users="$resources.sharedWith.data.users"
            :active-groups="$resources.sharedWithUserGroup.data"
            @add-new-users="addNewUsers"
          />

          <div class="overflow-y-auto px-4 sm:px-6">
            <div
              v-if="!$resources.sharedWith.loading"
              class="text-base space-y-4 mb-5"
            >
              <span class="text-gray-600 font-medium text-base">Users</span>
              <!-- Owner -->
              <div class="flex items-center gap-x-3">
                <Avatar
                  size="xl"
                  :label="$resources.sharedWith.data.owner.full_name"
                  :image="$resources.sharedWith.data.owner.user_image"
                />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    $resources.sharedWith.data.owner.full_name
                  }}</span>
                  <span class="text-gray-700">{{
                    $resources.sharedWith.data.owner.email
                  }}</span>
                </div>
                <span class="ml-auto flex items-center gap-1 text-gray-600">
                  Owner
                  <Diamond class="h-3.5" />
                </span>
              </div>
              <!-- Users -->
              <div
                v-for="(user, index) in $resources.sharedWith.data.users"
                :key="user.name"
                class="flex items-center gap-x-3"
              >
                <Avatar
                  size="xl"
                  :label="user.user_name"
                  :image="user.user_image"
                />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{
                    user.full_name ? user.full_name : user.user_name
                  }}</span>
                  <span class="text-gray-700">{{
                    user.full_name ? user.user_name : ""
                  }}</span>
                </div>
                <AccessButton
                  class="text-gray-700 relative flex-shrink-0 ml-auto"
                  :access-obj="user"
                  @update-access="
                    $resources.share.submit({
                      entity_name: entityName,
                      method: 'share',
                      user: user.user_name,
                      read: user.read,
                      write: user.write,
                      share: 0,
                      user_type: 'User',
                    })
                  "
                  @remove-access="
                    $resources.sharedWith.data.users.splice(index, 1),
                      $resources.share.submit({
                        entity_name: entityName,
                        method: 'unshare',
                        user: user.user_name,
                        user_type: 'User',
                      })
                  "
                />
              </div>
            </div>
            <!-- Groups -->
            <div
              v-if="$resources.sharedWithUserGroup.data?.length"
              class="text-base space-y-4 mb-5"
            >
              <span
                v-if="$resources.sharedWithUserGroup.data?.length"
                class="text-gray-600 font-medium text-base"
                >Groups</span
              >
              <div
                v-for="(group, index) in $resources.sharedWithUserGroup.data"
                :key="group.user_name"
                class="flex items-center gap-x-3"
              >
                <Avatar size="xl" :label="group.user_name" />
                <div class="flex items-start flex-col justify-start">
                  <span class="text-gray-900">{{ group.user_name }}</span>
                </div>
                <AccessButton
                  class="text-gray-700 relative flex-shrink-0 ml-auto"
                  :access-obj="group"
                  @update-access="
                    $resources.share.submit({
                      entity_name: entityName,
                      method: 'share',
                      user: group.user_name,
                      read: group.read,
                      write: group.write,
                      share: 0,
                      user_type: 'User Group',
                    })
                  "
                  @remove-access="
                    $resources.sharedWithUserGroup.data.splice(index, 1),
                      $resources.share.submit({
                        entity_name: entityName,
                        method: 'unshare',
                        user: group.user_name,
                        user_type: 'User Group',
                      })
                  "
                />
              </div>
            </div>
          </div>
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
            Copy Link
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
import { Avatar, Dialog, FeatherIcon, Switch } from "frappe-ui"
import AccessButton from "@/components/ShareDialog/AccessButton.vue"
import { getLink } from "@/utils/getLink"
import GeneralAccess from "@/components/GeneralAccess.vue"
import UserSearch from "@/components/ShareDialog/UserSearch.vue"
import Link from "@/components/EspressoIcons/Link.vue"
import Diamond from "@/components/EspressoIcons/Diamond.vue"
import Check from "@/components/EspressoIcons/Check.vue"

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
      generalAccess: {
        name: this.entityName,
        read: true,
        write: false,
        share: false,
        everyone: false,
        public: false,
      },
      allowComments: true,
      allowDownload: true,
      saveLoading: false,
      errorMessage: "",
      showAlert: false,
      alertMessage: "",
      entity: null,
      showSettings: false,
      searchUserText: "",
    }
  },
  computed: {
    accessMessage() {
      if (this.generalAccess.public) {
        return this.generalAccess.write
          ? "Anyone with a link to this file can edit"
          : "Anyone with a link to this file can view"
      }
      if (this.generalAccess.everyone) {
        return this.generalAccess.write
          ? `Members of ${this.$resources.getOrgName.data?.org_name} can edit`
          : `Members of ${this.$resources.getOrgName.data?.org_name} can view`
      } else {
        return "Only users with access can view or edit"
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
    generalAccess: {
      handler() {
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
      },
      deep: true,
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
  methods: {
    addNewUsers(data) {
      for (let i in data.users) {
        this.$resources.share.submit({
          entity_name: this.entityName,
          method: "share",
          user: data.users[i].user_name,
          user_type: data.users[i].user_type,
          read: data.access.read,
          write: data.access.write,
          share: 0,
        })
        if (data.users[i].user_type === "User") {
          this.$resources.sharedWith.data.users.push({
            user_name: data.users[i].user_name,
            read: data.access.read,
            write: data.access.write,
            share: 0,
            user_image: data.users[i].user_image,
            full_name: data.users[i].full_name,
          })
        } else {
          this.$resources.sharedWithUserGroup.data.push({
            user_name: data.users[i].user_name,
            read: data.access.read,
            write: data.access.write,
            share: 0,
          })
        }
      }
    },
    getLink,
  },
  resources: {
    sharedWith() {
      return {
        url: "drive.api.permissions.get_shared_with_list",
        params: {
          entity_name: this.entityName,
        },
        auto: true,
      }
    },
    sharedWithUserGroup() {
      return {
        url: "drive.api.permissions.get_shared_user_group_list",
        params: {
          entity_name: this.entityName,
        },
        auto: true,
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
          this.allowComments = !!data.allow_comments
          this.allowDownload = !!data.allow_download
        },
        auto: true,
      }
    },
    generalAccess() {
      return {
        url: "drive.api.permissions.get_general_access",
        params: { entity_name: this.entityName },
        onSuccess(data) {
          if (data[0]) {
            this.generalAccess = data[0]
          }
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
