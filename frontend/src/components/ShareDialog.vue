<template>
  <Dialog
    v-model="open"
    :options="{ title: `Share '${$resources.entity.data?.title}'` }">
    <template #body-content>
      <div ref="dialogContent" class="text-left min-w-[16rem]">
        <div class="border rounded-xl py-2 px-[18px]">
          <div class="flex flex-row">
            <div class="flex my-auto">
              <FeatherIcon
                name="globe"
                :stroke-width="2"
                class="h-5 text-yellow-600" />
            </div>
            <div class="grow ml-4">
              <div class="text-[14px] font-medium text-gray-900">
                Public access
              </div>
              <p class="text-base text-gray-700">{{ accessMessage }}</p>
            </div>
            <div class="flex my-auto">
              <Switch
                v-model="generalAccess.read"
                :class="generalAccess.read ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-[26px] items-center rounded-full"
                @click="updateAccess({ read: !generalAccess.read })">
                <span
                  :class="
                    generalAccess.read ? 'translate-x-3.5' : 'translate-x-1'
                  "
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>
          <div v-if="generalAccess.read" class="flex flex-row mt-3">
            <div class="grow text-[14px] text-gray-900">Allow edit</div>
            <div class="flex my-auto">
              <Switch
                v-model="generalAccess.write"
                :class="generalAccess.write ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-[26px] items-center rounded-full"
                @click="updateAccess({ write: !generalAccess.write })">
                <span
                  :class="
                    generalAccess.write ? 'translate-x-3.5' : 'translate-x-1'
                  "
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>

          <div v-if="generalAccess.read" class="flex flex-row mt-2">
            <div class="grow text-[14px] text-gray-900">Allow download</div>
            <div class="flex my-auto">
              <Switch
                v-model="allowDownload"
                :class="allowDownload ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-[26px] items-center rounded-full"
                @click="$resources.toggleAllowDownload.submit()">
                <span
                  :class="allowDownload ? 'translate-x-3.5' : 'translate-x-1'"
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>
        </div>
        <div class="border rounded-xl py-2 px-2 mt-5">
          <UserSearch
            @submit="
              ({ user, write }) =>
                $resources.share.submit({
                  method: 'share',
                  entity_name: entityName,
                  user,
                  write,
                  share: 1,
                })
            " />
          <ErrorMessage
            v-if="$resources.share.error"
            class="mt-2"
            :message="errorMessage" />

          <div
            v-if="$resources.sharedWith.data?.length > 0"
            class="flex flex-row mt-3">
            <div class="grow text-[14px] text-gray-900">Allow comments</div>
            <div class="flex my-auto">
              <Switch
                v-model="allowComments"
                :class="allowComments ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-[26px] items-center rounded-full"
                @click="$resources.toggleAllowComments.submit()">
                <span
                  :class="allowComments ? 'translate-x-3.5' : 'translate-x-1'"
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>

          <div
            v-if="$resources.sharedWith.data?.length > 0"
            class="flex mt-5 text-[14px] text-gray-600">
            Members
          </div>
          <div
            v-for="user in $resources.sharedWith.data"
            :key="user.user"
            class="mt-3 flex flex-row w-full gap-2 items-center antialiased">
            <div class="overflow-hidden rounded-full h-9 w-9">
              <img
                v-if="user.user_image"
                :src="user.user_image"
                class="object-cover rounded-full h-7 w-7" />
              <div
                v-else
                class="flex items-center justify-center w-full h-full text-base text-gray-600 uppercase bg-gray-200">
                {{ user.full_name[0] }}
              </div>
            </div>
            <div class="grow truncate">
              <div class="text-gray-900 text-[14px] font-medium">
                {{ user.full_name }}
              </div>
              <div class="text-gray-600 text-base">{{ user.user }}</div>
            </div>
            <Popover transition="default">
              <template #target="{ togglePopover }">
                <Button
                  icon-right="chevron-down"
                  :loading="user.loading"
                  class="text-sm focus:ring-0 focus:ring-offset-0 text-gray-700 text-[13px] rounded-lg"
                  appearance="minimal"
                  @click="togglePopover()">
                  {{ user.write ? "Can edit" : "Can view" }}
                </Button>
              </template>
              <template #body-main="{ togglePopover }">
                <div class="p-1">
                  <div
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
                  </div>
                </div>
              </template>
            </Popover>
          </div>
        </div>
        <div class="flex mt-5">
          <Button
            icon-left="link"
            appearance="white"
            class="h-7 rounded-lg"
            @click="getLink">
            Copy link
          </Button>
          <Button
            appearance="minimal"
            class="ml-auto text-gray-700 hover:bg-white focus:bg-white active:bg-white h-7 rounded-lg"
            icon-right="info">
            Learn about sharing
          </Button>
        </div>
        <Alert v-if="showAlert" :title="alertMessage" class="mt-5"></Alert>
      </div>
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
} from "frappe-ui";
import { Switch } from "@headlessui/vue";
import UserSearch from "@/components/UserSearch.vue";

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
    };
  },
  computed: {
    accessChanged() {
      return (
        JSON.stringify(this.generalAccess) !==
        JSON.stringify(this.$resources.generalAccess.data)
      );
    },
    accessMessage() {
      if (this.generalAccess.read)
        return this.generalAccess.write
          ? "Anyone with the link can edit"
          : "Anyone with the link can view";
      return "Publish and share link with anyone";
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
  mounted() {
    const targetElement = this.$refs.dialogContent?.closest(".overflow-hidden");
    if (targetElement) {
      targetElement.classList.remove("overflow-hidden");
      targetElement.classList.add("self-center");
      targetElement.childNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE)
          node.classList.add("rounded-lg");
      });
    }
  },
  methods: {
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
        });
    },
    async getLink() {
      this.showAlert = false;
      const link = this.$resources.entity.data.is_group
        ? `${window.location.origin}/drive/folder/${this.entityName}`
        : `${window.location.origin}/drive/file/${this.entityName}`;
      try {
        await navigator.clipboard.writeText(link);
        this.alertMessage = "Link copied successfully";
        this.showAlert = true;
      } catch ($e) {
        this.alertMessage = "Some error occurred while copying the link";
        this.showAlert = true;
      }
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
    entity() {
      return {
        url: "drive.api.files.get_entity",
        params: {
          entity_name: this.entityName,
          fields: "title,is_group,allow_comments,allow_download",
        },
        onSuccess(data) {
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
        validate(params) {
          if (!params?.user) {
            return "No user was specified";
          }
        },
        onSuccess() {
          this.$resources.share.error = null;
          this.$resources.sharedWith.fetch();
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
        },
        onSuccess() {
          this.$resources.entity.fetch();
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
        },
        onSuccess() {
          this.$resources.entity.fetch();
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
