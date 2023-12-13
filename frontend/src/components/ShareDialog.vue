<template>
  <Dialog v-model="open" :options="{ size: 'lg' }">
    <template #body-title>
      <div class="flex items-center justify-start w-full">
        <span class="font-semibold text-2xl">Sharing</span>
        <div
          class="flex items-center justify-start border pl-0.5 pr-2 py-0.5 ml-1 rounded-sm border-gray-400 max-w-[80%]">
          <Folder
            class="h-4 stroke-[1.5] text-gray-900"
            v-if="$resources.entity.data?.is_group" />
          <File class="h-4 stroke-[1.5] text-gray-900" v-else />
          <span
            class="font-medium text-base text-gray-800 line-clamp-1 truncate max-w-[90%]">
            {{ $resources.entity.data?.title }}
          </span>
        </div>
      </div>
    </template>
    <template #body-content>
      <div class="mb-5">
        <div class="flex flex-row">
          <FeatherIcon
            v-if="generalAccess.public"
            name="globe"
            :stroke-width="1.5"
            class="h-5 text-red-500 my-auto mr-2" />

          <Building2
            v-if="generalAccess.everyone"
            name="building"
            :stroke-width="1.5"
            class="h-5 text-blue-600 my-auto mr-2" />

          <FeatherIcon
            v-if="
              (generalAccess.everyone == false) &
              (generalAccess.public == false)
            "
            name="lock"
            :stroke-width="1.5"
            class="h-5 text-gray-600 my-auto mr-2" />

          <Popover transition="default">
            <template #target="{ togglePopover }">
              <Button appearance="minimal" @click="togglePopover()">
                <template #suffix>
                  <ChevronsUpDown class="w-4" />
                </template>
                {{
                  generalAccess.public
                    ? "Public Access"
                    : generalAccess.everyone
                    ? "Organization Access"
                    : "Restricted Access"
                }}
              </Button>
            </template>
            <template #body-main="{ togglePopover }">
              <div class="flex flex-col p-1">
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded p-1"
                  variant="ghost"
                  @click="
                    generalAccess.read = false;
                    generalAccess.everyone = false;
                    generalAccess.public = false;
                    generalAccess.share = false;
                    togglePopover();
                  ">
                  Restricted Access
                  <Check v-if="!generalAccess.read" class="h-4" />
                </div>
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded p-1"
                  variant="ghost"
                  @click="
                    generalAccess.read = true;
                    generalAccess.everyone = true;
                    generalAccess.public = false;
                    generalAccess.share = false;
                    togglePopover();
                  ">
                  Organization Access
                  <Check v-if="generalAccess.everyone" class="h-4" />
                </div>
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded p-1"
                  variant="ghost"
                  @click="
                    generalAccess.read = true;
                    generalAccess.everyone = false;
                    generalAccess.public = true;
                    generalAccess.share = false;
                    togglePopover();
                  ">
                  Public Access
                  <Check v-if="generalAccess.public" class="h-4" />
                </div>
              </div>
            </template>
          </Popover>
          <div v-if="generalAccess.read" class="flex ml-auto my-auto">
            <Popover transition="default">
              <template #target="{ togglePopover }">
                <Button appearance="minimal" @click="togglePopover()">
                  <template #suffix>
                    <ChevronsUpDown class="w-4" />
                  </template>
                  {{ generalAccess.write ? "Can edit" : "Can view" }}
                </Button>
              </template>
              <template #body-main="{ togglePopover }">
                <div class="flex flex-col p-1">
                  <div
                    class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      generalAccess.read = true;
                      generalAccess.write = false;
                      togglePopover();
                    ">
                    Can view
                    <Check
                      v-if="generalAccess.read && !generalAccess.write"
                      class="h-4 ml-2" />
                  </div>
                  <div
                    class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      generalAccess.read = true;
                      generalAccess.write = true;
                      togglePopover();
                    ">
                    Can edit
                    <Check v-if="generalAccess.write" class="h-4 ml-2" />
                  </div>
                </div>
              </template>
            </Popover>
          </div>
        </div>
        <span class="pl-9.5 py-2 text-base text-gray-700">
          {{ accessMessage }}
        </span>
      </div>
      <UserSearch
        :search-groups="true"
        place-holder-text="Search for users or emails"
        @submit="
          (user) =>
            $resources.share.submit({
              method: 'share',
              entity_name: entityName,
              user_type: user.email ? 'User' : 'User Group',
              user: user.email ? user.email : user.name,
            })
        " />
      <ErrorMessage
        v-if="$resources.share.error"
        class="mt-2"
        :message="errorMessage" />

      <div
        v-if="
          generalAccess.read ||
          $resources.sharedWith.data?.users.length ||
          $resources.sharedWithUserGroup.data?.length
        ">
        <div class="flex mt-5 text-base text-gray-600">Global permissions</div>
        <div class="flex flex-row mt-2">
          <FeatherIcon class="w-4 text-gray-700 mr-1" name="message-square" />
          <div class="grow text-[14px] text-gray-800">Comment</div>
          <div class="flex my-auto">
            <Switch
              v-model="allowComments"
              :class="allowComments ? 'bg-black' : 'bg-gray-200'"
              class="relative inline-flex h-4 w-[26px] items-center rounded-full"
              @click="toggleComments">
              <span
                :class="allowComments ? 'translate-x-3.5' : 'translate-x-1'"
                class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
            </Switch>
          </div>
        </div>
        <div class="flex flex-row mt-2">
          <FeatherIcon class="w-4 text-gray-700 mr-1" name="download" />
          <div class="grow text-[14px] text-gray-800">Download</div>
          <div class="flex my-auto">
            <Switch
              v-model="allowDownload"
              :class="allowDownload ? 'bg-black' : 'bg-gray-200'"
              class="relative inline-flex h-4 w-[26px] items-center rounded-full"
              @click="toggleDownload">
              <span
                :class="allowDownload ? 'translate-x-3.5' : 'translate-x-1'"
                class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
            </Switch>
          </div>
        </div>
      </div>
      <div class="flex mt-5 text-base text-gray-600">Users with access</div>
      <div v-if="!$resources.entity.loading" class="flex flex-col">
        <div
          v-if="$resources.sharedWith.data?.owner"
          class="mt-1 flex flex-row w-full gap-2 items-center hover:bg-gray-50 rounded cursor-pointer group">
          <Avatar
            :image="$resources.sharedWith.data?.owner.user_image"
            :label="$resources.sharedWith.data?.owner.full_name"
            size="xl" />
          <div class="grow truncate">
            <div class="text-gray-900 text-[14px] font-medium">
              {{ $resources.sharedWith.data?.owner.full_name }}
            </div>
            <div class="text-gray-600 text-base">
              {{ $resources.sharedWith.data?.owner.email }}
            </div>
          </div>
          <Button variant="minimal" class="text-gray-600">Owner</Button>
        </div>
        <template v-if="$resources.sharedWith.data?.users">
          <div
            v-for="user in $resources.sharedWith.data.users"
            :key="user.user_name"
            class="mt-1 flex flex-row w-full gap-2 items-center hover:bg-gray-50 rounded py-2 cursor-pointer group">
            <Avatar
              :image="user.user_image"
              :label="user.full_name"
              size="xl" />
            <div class="grow truncate">
              <div class="text-gray-900 text-[14px] font-medium">
                {{ user.full_name }}
              </div>
              <div class="text-gray-600 text-base">{{ user.user_name }}</div>
            </div>
            <Popover transition="default">
              <template #target="{ togglePopover }">
                <Button
                  :loading="user.loading"
                  class="text-sm focus:ring-0 focus:ring-offset-0 text-gray-700"
                  appearance="minimal"
                  @click="togglePopover()">
                  <template #prefix>
                    <ChevronsUpDown class="w-4" />
                  </template>
                  {{ user.write ? "Can edit" : "Can view" }}
                </Button>
              </template>
              <template #body-main="{ togglePopover }">
                <div class="p-1">
                  <div
                    class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      $resources.share
                        .submit({
                          entity_name: entityName,
                          method: 'share',
                          user: user.user_name,
                          write: 0,
                          share: 0,
                        })
                        .then(togglePopover())
                    ">
                    Can view
                    <Check v-if="!user.write" class="h-4 ml-2" />
                  </div>
                  <div
                    class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      $resources.share
                        .submit({
                          entity_name: entityName,
                          method: 'share',
                          user: user.user_name,
                          write: 1,
                          share: 0,
                        })
                        .then(togglePopover())
                    ">
                    Can edit
                    <Check v-if="user.write" class="h-4 ml-2" />
                  </div>
                  <!-- <div
                      class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                      @click="$resources.share.submit({
                          entity_name: entityName,
                          method: 'share',
                          user: user.user,
                          write: 1,
                          share: 1,
                        })
                        .then(togglePopover())">
                     Can share
                     <Check v-if="generalAccess.write" class="h-4 ml-2"/>
                    </div> -->
                  <div
                    class="flex w-full items-center justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      $resources.share
                        .submit({
                          entity_name: entityName,
                          method: 'unshare',
                          user: user.user_name,
                        })
                        .then(togglePopover())
                    ">
                    Remove
                  </div>
                </div>
              </template>
            </Popover>
          </div>
        </template>
      </div>

      <div
        v-if="$resources.sharedWithUserGroup.data?.length"
        class="flex flex-col">
        <div class="flex mt-5 text-base text-gray-600">Groups with access</div>
        <div
          v-for="group in $resources.sharedWithUserGroup.data"
          :key="group"
          class="mt-3 flex flex-row w-full gap-2 items-center">
          <Avatar size="xl" :label="group.user_name"></Avatar>
          <div
            class="text-gray-900 text-[14px] self-center font-medium grow truncate">
            {{ group.user_name }}
          </div>
          <Popover transition="default">
            <template #target="{ togglePopover }">
              <Button
                :loading="group.loading"
                class="text-sm focus:ring-0 focus:ring-offset-0 text-gray-700"
                appearance="minimal"
                @click="togglePopover()">
                <template #prefix>
                  <ChevronsUpDown class="w-4" />
                </template>
                {{ group.write ? "Can edit" : "Can view" }}
              </Button>
            </template>
            <template #body-main="{ togglePopover }">
              <div class="p-1">
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                  @click="
                    $resources.share
                      .submit({
                        entity_name: entityName,
                        method: 'share',
                        user: group.user_name,
                        user_type: 'User Group',
                        write: 0,
                        share: 0,
                      })
                      .then(togglePopover())
                  ">
                  Can view
                  <Check v-if="!group.write" class="h-4 ml-2" />
                </div>
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                  @click="
                    $resources.share
                      .submit({
                        entity_name: entityName,
                        method: 'share',
                        user: group.user_name,
                        user_type: 'User Group',
                        write: 1,
                        share: 0,
                      })
                      .then(togglePopover())
                  ">
                  Can edit
                  <Check v-if="group.write" class="h-4 ml-2" />
                </div>
                <div
                  class="flex w-full items-center justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                  @click="
                    $resources.share
                      .submit({
                        entity_name: entityName,
                        method: 'unshare',
                        user: group.user_name,
                        user_type: 'User Group',
                      })
                      .then(togglePopover())
                  ">
                  Remove
                </div>
              </div>
            </template>
          </Popover>
        </div>
      </div>
      <div class="w-full flex items-center justify-between mt-8">
        <Button
          :variant="'subtle'"
          icon-left="link-2"
          @click.native="getLink(entity)">
          Copy Link
        </Button>
        <Button variant="solid" @click="submit">
          <template #prefix>
            <Share2 class="w-4" />
          </template>
          Share
        </Button>
      </div>
      <Alert v-if="showAlert" :title="alertMessage" class="mt-5" />
    </template>
  </Dialog>
</template>
<script>
import {
  Dialog,
  ErrorMessage,
  FeatherIcon,
  Button,
  Alert,
  Popover,
  Avatar,
} from "frappe-ui";
import { Switch } from "@headlessui/vue";
import UserSearch from "@/components/UserSearch.vue";
import { MessagesSquare } from "lucide-vue-next";
import MessageCircleOff from "@/components/message-circle-off.vue";
import { MessageCircle } from "lucide-vue-next";
import { ArrowDownToLine } from "lucide-vue-next";
import ArrowDownToLineOff from "@/components/arrow-down-to-line-off.vue";
import { Link } from "lucide-vue-next";
import { Building2 } from "lucide-vue-next";
import { ChevronsUpDown } from "lucide-vue-next";
import { Check } from "lucide-vue-next";
import { Trash } from "lucide-vue-next";
import { toast } from "@/utils/toasts.js";
import { getLink } from "@/utils/getLink";
import FrappeFolderLine from "@/components/FrappeFolderLine.vue";
import FrappeFileLine from "@/components/FrappeFileLine.vue";
import { Share2 } from "lucide-vue-next";
import { Folder } from "lucide-vue-next";
import { File } from "lucide-vue-next";

export default {
  name: "ShareDialog",
  components: {
    Dialog,
    ErrorMessage,
    FeatherIcon,
    Button,
    UserSearch,
    Alert,
    Switch,
    Popover,
    MessagesSquare,
    MessageCircleOff,
    MessageCircle,
    ArrowDownToLine,
    ArrowDownToLineOff,
    Link,
    toast,
    Building2,
    ChevronsUpDown,
    Check,
    Avatar,
    Trash,
    FrappeFileLine,
    FrappeFolderLine,
    Share2,
    Folder,
    File,
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
  data() {
    return {
      generalAccess: {
        name: "",
        read: false,
        write: false,
        share: false,
        everyone: false,
        public: false,
      },
      allowComments: false,
      allowDownload: false,
      saveLoading: false,
      errorMessage: "",
      showAlert: false,
      alertMessage: "",
      entity: null,
    };
  },
  computed: {
    accessMessage() {
      if (this.generalAccess.public) {
        return this.generalAccess.write
          ? "Anyone with a link to this file can edit"
          : "Anyone with a link to this file can view";
      }
      if (this.generalAccess.everyone) {
        return this.generalAccess.write
          ? `All users in ${this.$resources.getOrgName.data?.org_name} can edit`
          : `All users in ${this.$resources.getOrgName.data?.org_name} can view`;
      } else {
        return "Only users and groups with access can view or edit";
      }
    },
    accessChanged() {
      return (
        JSON.stringify(this.generalAccess) !==
        JSON.stringify(this.$resources.generalAccess.data)
      );
    },
    open: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
        if (!value) {
          this.errorMessage = "";
        }
      },
    },
  },
  methods: {
    submit() {
      if (this.allowComments != this.$resources.entity.data.allow_comments) {
        this.$resources.toggleAllowComments.submit();
      }
      if (this.allowDownload != this.$resources.entity.data.allow_download) {
        this.$resources.toggleAllowDownload.submit();
      }
      this.$resources.updateAccess.submit({
        method: "set_general_access",
        entity_name: this.entityName,
        read: this.generalAccess.read,
        write: this.generalAccess.write,
        share_name: this.generalAccess.name,
        share: this.generalAccess.share,
        public: this.generalAccess.public,
        everyone: this.generalAccess.everyone,
      });
      this.open = false;
      this.$emit("success");
    },
    toggleComments() {
      toast({
        title: this.allowComments
          ? "Comments turned off"
          : "Comments turned on",
        text: this.allowComments
          ? "Users cannot read and write comments"
          : "Users can read and write comments",
        /* icon: "message-circle", */
        position: "bottom-right",
        iconClasses: "text-black-500",
        timeout: 2,
      });
      this.allowComments = !this.allowComments;
    },
    toggleDownload() {
      toast({
        title: this.allowDownload
          ? "Downloading turned off"
          : "Downloading turned on",
        text: this.allowDownload
          ? "Users cannot download file"
          : "Users can download file",
        /* icon: "download", */
        position: "bottom-right",
        iconClasses: "text-black-500",
        timeout: 1,
      });
      this.allowDownload = !this.allowDownload;
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
      };
    },
    sharedWithUserGroup() {
      return {
        url: "drive.api.permissions.get_shared_user_group_list",
        params: {
          entity_name: this.entityName,
        },
        auto: true,
      };
    },
    entity() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        params: {
          entity_name: this.entityName,
          fields: "title,is_group,allow_comments,allow_download,owner",
        },
        onSuccess(data) {
          this.entity = data;
          this.allowComments = !!data.allow_comments;
          this.allowDownload = !!data.allow_download;
        },
        auto: true,
      };
    },
    generalAccess() {
      return {
        url: "drive.api.permissions.get_general_access",
        params: { entity_name: this.entityName },
        onSuccess(data) {
          if (data[0]) {
            this.generalAccess = data[0];
          }
        },
        auto: true,
      };
    },
    share() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          method: "share",
          entity_name: this.entityName,
        },
        onSuccess() {
          this.$resources.share.error = null;
          this.$resources.sharedWith.fetch();
          this.$resources.sharedWithUserGroup.fetch();
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
      };
    },
    toggleAllowComments() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          entity_name: this.entityName,
          method: "toggle_allow_comments",
          new_value: this.allowComments,
        },
        onSuccess() {
          this.$emit("success");
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
    toggleAllowDownload() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          entity_name: this.entityName,
          method: "toggle_allow_download",
          new_value: this.allowDownload,
        },
        onSuccess() {
          this.$emit("success");
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
    updateAccess() {
      return {
        url: "drive.api.files.call_controller_method",
        onSuccess() {
          this.$resources.generalAccess.fetch();
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
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
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
        auto: true,
      };
    },
  },
};
</script>
