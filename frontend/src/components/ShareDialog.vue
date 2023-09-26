<template>
  <Dialog
    v-model="open"
    :options="{
      title: `Share '${$resources.entity.data?.title}'`,
      size: 'lg',
    }">
    <template #body-content>
      <div class="pt-2 pb-2 mb-4">
        <div class="flex flex-row pl-2">
          <FeatherIcon
            v-if="generalAccess.read || generalAccess.write"
            name="globe"
            :stroke-width="2"
            class="h-5 text-red-500 my-auto mr-2" />

          <FeatherIcon
            v-else
            name="lock"
            :stroke-width="2"
            class="h-5 text-gray-600 my-auto mr-2" />

          <!-- <Building2
                name="building"
                :stroke-width="2"
                class="h-5 text-green-600 my-auto"
                />  -->

          <Popover transition="default">
            <template #target="{ togglePopover }">
              <Button appearance="minimal" @click="togglePopover()">
                <template #suffix>
                  <ChevronsUpDown class="w-4" />
                </template>
                {{ generalAccess.read ? "Public Access" : "Restricted Access" }}
              </Button>
            </template>
            <template #body-main="{ togglePopover }">
              <div class="flex flex-col p-1">
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded p-1"
                  variant="ghost"
                  @click="
                    (generalAccess = {
                      read: false,
                      write: false,
                      share: false,
                    }),
                      togglePopover()
                  ">
                  Restricted Acess
                  <Check v-if="!generalAccess.read" class="h-4" />
                </div>
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded p-1"
                  variant="ghost"
                  @click="
                    (generalAccess = {
                      read: true,
                      write: false,
                      share: false,
                    }),
                      togglePopover()
                  ">
                  Public Access
                  <Check v-if="generalAccess.read" class="h-4" />
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
                      (generalAccess = {
                        read: true,
                        write: false,
                        share: false,
                      }),
                        togglePopover()
                    ">
                    Can view
                    <Check
                      v-if="generalAccess.read && !generalAccess.write"
                      class="h-4 ml-2" />
                  </div>
                  <div
                    class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                    @click="
                      (generalAccess = {
                        read: true,
                        write: true,
                        share: false,
                      }),
                        togglePopover()
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
        :search-groups="false"
        place-holder-text="Search for users or emails"
        @submit="
          (user) =>
            $resources.share.submit({
              method: 'share',
              entity_name: entityName,
              is_user_group: user.email ? false : true,
              user: user.email ? user.email : user.name,
            })
        " />
      <ErrorMessage
        v-if="$resources.share.error"
        class="mt-2"
        :message="errorMessage" />

      <div class="flex mt-5 text-base text-gray-600">Users with access</div>
      <div v-if="!$resources.entity.loading" class="flex flex-col">
        <div
          v-for="user in $resources.sharedWith.data"
          :key="user.user"
          class="mt-1 flex flex-row w-full gap-2 items-center hover:bg-gray-50 rounded py-2 px-1 cursor-pointer group">
          <Avatar :image="user.user_image" :label="user.full_name" size="xl" />
          <div class="grow truncate">
            <div class="text-gray-900 text-[14px] font-medium">
              {{ user.full_name }}
            </div>
            <div class="text-gray-600 text-base">{{ user.user }}</div>
          </div>
          <Button
            v-if="user.user === entity.owner"
            variant="minimal"
            class="text-gray-600">
            Owner
          </Button>
          <Popover v-else transition="default">
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
                <!-- <div
                    v-for="item in ['Viewer', 'Editor', 'Remove']"
                    :key="item">
                    <div
                      class="text-gray-900 text-[13px] hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                      @click="
                        () => {
                          user.loading = true;
                          $resources.share
                            .submit(
                              Object.assign(
                                {
                                  method:
                                    item === 'Remove' ? 'unshare' : 'share',
                                  entity_name: entityName,
                                  user: user.user,
                                },
                                item != 'Remove' && {
                                  write: item === 'Editor' ? 1 : 0,
                                }
                              )
                            )
                            .then(() => {
                              user.loading = false;
                            });
                          togglePopover();
                        }
                      ">
                      {{ item }}
                    </div>
                  </div> -->
                <div
                  class="flex w-full justify-between text-gray-900 text-base hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                  @click="
                    $resources.share
                      .submit({
                        entity_name: entityName,
                        method: 'share',
                        user: user.user,
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
                        user: user.user,
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
                        method: 'set_general_access',
                        entity_name: entityName,
                        method: 'unshare',
                        user: user.user,
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

      <div
        v-if="$resources.sharedWithUserGroup.data?.length"
        class="flex flex-col">
        <div class="flex mt-5 text-base text-gray-600">Groups with access</div>
        <div
          v-for="group in $resources.sharedWithUserGroup.data"
          :key="group"
          class="mt-3 flex flex-row w-full gap-2 items-center space-y-2">
          <Avatar size="xl" :label="group"></Avatar>
          <div class="grow truncate">
            <div class="text-gray-900 text-[14px] font-medium">
              {{ group }}
            </div>
            <div class="text-gray-600 text-base">{{ group }}</div>
          </div>
        </div>
      </div>

      <div class="flex justify-items-center content-center mt-6">
        <div class="flex justify-items-center content-center">
          <Button variant="ghost" @click="getLink">
            <Link class="w-4" />
          </Button>
          <div class="border h-7 mx-1"></div>
          <Button
            v-model="allowComments"
            variant="ghost"
            @click="toggleComments">
            <MessageCircle v-if="allowComments" class="w-4" />
            <MessageCircleOff v-else class="w-4" />
          </Button>
          <Button
            v-model="allowDownload"
            variant="ghost"
            @click="toggleDownload">
            <ArrowDownToLine v-if="allowDownload" class="w-4" />
            <ArrowDownToLineOff v-else class="w-4" />
          </Button>
        </div>
        <Button variant="solid" @click="submit" class="ml-auto px-8">
          Share
        </Button>
      </div>
      <Alert v-if="showAlert" :title="alertMessage" class="mt-5"></Alert>
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
  toast,
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
      generalAccess: {},
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
      if (this.generalAccess.read) {
        return this.generalAccess.write
          ? "Anyone with the link can edit"
          : "Anyone with the link can view";
      } else {
        return "Only users with access can view this file";
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
      this.$resources.updateAccess.submit({
        method: "set_general_access",
        entity_name: this.entityName,
        new_access: this.generalAccess,
      });
      this.open = false;
    },
    toggleComments() {
      toast({
        title: this.allowComments
          ? "Comments turned off"
          : "Comments turned on",
        text: this.allowComments
          ? "Users cannot read and write comments"
          : "Users can read and write comments",
        icon: "message-circle",
        position: "bottom-right",
        iconClasses: "text-black-500",
      });
      this.allowComments = !this.allowComments;
    },
    toggleDownload() {
      toast({
        title: this.allowDownload
          ? "Downloading turned off"
          : "Downloading turned on",
        text: this.allowDownload
          ? "Users cannot download this"
          : "Users can download this",
        icon: "download",
        position: "bottom-right",
        iconClasses: "text-black-500",
      });
      this.allowDownload = !this.allowDownload;
    },
    updateAccess(updatedAccess) {
      this.saveLoading = true;
      const newAccess = { ...this.generalAccess, ...updatedAccess };
      this.$resources.updateAccess
        .submit({
          method: "set_general_access",
          entity_name: this.entityName,
          new_access: newAccess,
        })
        .then(() => {
          this.saveLoading = false;
          this.$resources.toggleAllowDownload.submit();
          this.$resources.toggleAllowComments.submit();
        });
    },
    async getLink() {
      this.showAlert = false;
      const link = this.$resources.entity.data.is_group
        ? `${window.location.origin}/drive/folder/${this.entityName}`
        : `${window.location.origin}/drive/file/${this.entityName}`;
      await navigator.clipboard.writeText(link);
      toast({
        title: "Done",
        text: "Copied Link!",
        icon: "check",
        position: "bottom-right",
        iconClasses: "text-blue-500",
      });
    },
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
        url: "drive.api.files.get_entity",
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
          data = data || {};
          data.read = !!data.read;
          data.write = !!data.write;
          this.$resources.generalAccess.data = data;
          this.generalAccess = Object.assign({}, data);
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
          value: this.allowComments,
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
          value: this.allowDownload,
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
  },
};
</script>
