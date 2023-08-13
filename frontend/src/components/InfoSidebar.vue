<template>
  <Transition
    enter-from-class="translate-x-[150%] opacity-0"
    leave-to-class="translate-x-[150%] opacity-0"
    enter-active-class="transition duration-125"
    leave-active-class="transition duration-125">
    <div
      v-if="showInfoSidebar"
      class="min-w-[350px] max-w-[350px] min-h-full border-l overflow-auto">
      <div v-if="entity" class="w-full border-b p-4 overflow-visible">
        <div class="flex items-center">
          <svg
            v-if="entity.is_group"
            :style="{ fill: entity.color }"
            :draggable="false"
            class="h-5 mr-2.5"
            viewBox="0 0 40 40"
            xmlns="http://www.w3.org/2000/svg">
            <path
              d="M19.8341 7.71154H3C2.72386 7.71154 2.5 7.9354 2.5 8.21154V34.75C2.5 35.8546 3.39543 36.75 4.5 36.75H35.5C36.6046 36.75 37.5 35.8546 37.5 34.75V4.75C37.5 4.47386 37.2761 4.25 37 4.25H24.7258C24.6719 4.25 24.6195 4.26739 24.5764 4.29957L20.133 7.61239C20.0466 7.67676 19.9418 7.71154 19.8341 7.71154Z" />
          </svg>
          <img
            v-else
            :src="getIconUrl(formatMimeType(entity.mime_type))"
            :draggable="false"
            class="h-5 mr-2.5" />
          <div class="font-medium truncate text-xl">
            {{ entity.title }}
          </div>
        </div>
      </div>
      <div v-if="entity">
        <div v-if="tab === 0" class="h-full pb-12">
          <div
            class="p-4 border-b z-10 sticky top-0 bg-white"
            :class="
              tab === 0
                ? 'flex-auto'
                : 'text-gray-600 cursor-pointer flex-none '
            "
            @click="tab = 0">
            <div class="flex items-center">
              <FeatherIcon name="alert-circle" class="h-4 mr-2 stroke-2" />
              <span class="font-medium text-lg">Info</span>
            </div>
          </div>
          <div
            class="relative p-4 min-h-full flex-auto flex flex-col overflow-y-auto">
            <FileRender
              v-if="
                $store.state.entityInfo.mime_type?.startsWith('image') &&
                showInfoSidebar
              "
              class="border-2"
              :preview-entity="entity" />
          </div>
          <div class="p-4 space-y-4">
            <div v-if="entity.owner === 'me'">
              <div class="text-lg font-medium mb-2">Manage Access</div>
              <div class="flex flex-row">
                <Button class="h-7" @click="showShareDialog = true">
                  Share
                </Button>
              </div>
            </div>
            <div
              v-if="
                entity.owner === 'me' || $resources.entityTags.data?.length
              ">
              <div class="text-lg font-medium my-2">Tag</div>
              <div class="flex flex-wrap gap-2">
                <Tag
                  v-for="tag in $resources.entityTags.data"
                  :key="tag"
                  :tag="tag"
                  :entity="entity"
                  @success="
                    () => {
                      $resources.userTags.fetch();
                      $resources.entityTags.fetch();
                    }
                  " />
                <Button
                  v-if="!addTag && entity.owner === 'me'"
                  class="h-6 text-[12px] text-gray-800"
                  icon-left="plus"
                  @click="addTag = true">
                  Add tag
                </Button>
              </div>

              <TagInput
                v-if="addTag"
                :class="{ 'mt-2': $resources.entityTags.data.length }"
                :entity="entity"
                :unadded-tags="unaddedTags"
                @success="
                  () => {
                    $resources.userTags.fetch();
                    $resources.entityTags.fetch();
                    addTag = false;
                  }
                "
                @close="addTag = false" />
            </div>
            <div class="text-lg font-medium my-3">General Info</div>
            <div class="flex text-base">
              <div class="w-1/2 text-gray-600 space-y-2">
                <div>Type</div>
                <div>Size</div>
                <div>Modified</div>
                <div>Created</div>
                <div>Owner</div>
              </div>
              <div class="w-1/2 space-y-2">
                <div>{{ formattedMimeType }}</div>
                <div>{{ entity.file_size }}</div>
                <div>{{ entity.modified }}</div>
                <div>{{ entity.creation }}</div>
                <div>{{ entity.owner }}</div>
              </div>
            </div>
            <div class="text-gray-600 text-base">
              Viewers can download this file.
            </div>
          </div>
        </div>
        <div v-if="tab === 1" class="h-full pb-12">
          <div
            v-if="tab === 1"
            class="z-10 p-4 border-b sticky top-0 bg-white"
            :class="tab === 1 ? 'flex-auto' : 'text-gray-600 cursor-pointer'"
            @click="tab = 1">
            <div class="flex items-center">
              <FeatherIcon name="message-circle" class="h-4 mr-2 stroke-2" />
              <span class="font-medium text-lg">Comments</span>
            </div>
          </div>
          <div
            v-if="entity.allow_comments"
            class="space-y-6 px-4 overflow-y-auto pb-4">
            <div
              v-for="comment in $resources.comments.data"
              :key="comment"
              class="flex gap-3 my-4 items-center">
              <Avatar
                :label="comment.comment_by"
                :image="comment.user_image"
                class="h-7 w-7" />
              <div>
                <span class="my-1">
                  <span class="text-sm font-medium">
                    {{ comment.comment_by }}
                  </span>
                  <span class="text-gray-500 text-sm">{{ " ∙ " }}</span>
                  <span class="text-gray-700 text-sm">
                    {{ comment.creation }}
                  </span>
                </span>
                <div class="text-base text-gray-700">
                  {{ comment.content }}
                </div>
              </div>
            </div>
            <div v-if="userId != 'Guest'" class="flex items-center gap-3 my-4">
              <Avatar :label="fullName" :image="imageURL" class="h-7 w-7" />
              <div class="flex">
                <Input
                  v-model="newComment"
                  type="text"
                  placeholder="Add comment"
                  @keydown.enter="postComment" />
              </div>
              <Button @click="postComment" variant="solid">Add</Button>
            </div>
          </div>

          <div v-else class="text-gray-600 text-base mt-2 p-4">
            Comments have been disabled for this
            {{ entity.is_group ? "folder" : "file" }} by its owner.
          </div>
        </div>
      </div>
      <div
        v-else
        class="flex h-full w-full flex-col items-center justify-center rounded-lg text-center">
        <svg viewBox="0 0 78 85" class="w-1/6 fill-transparent stroke-2 pb-6">
          <path
            d="M42 31H66 M42 51H66 M42 25H55 M42 45H55 M65 9V8C65 4.13401 61.866 1 58 1H8C4.13401 1 1 4.13401 1 8V66C1 69.866 4.13401 73 8 73H10 M70 12H20C16.134 12 13 15.134 13 19V77C13 80.866 16.134 84 20 84H70C73.866 84 77 80.866 77 77V19C77 15.134 73.866 12 70 12Z"
            stroke="#404040" />
          <path
            d="M32 43H26C24.8954 43 24 43.8954 24 45V51C24 52.1046 24.8954 53 26 53H32C33.1046 53 34 52.1046 34 51V45C34 43.8954 33.1046 43 32 43Z M32 23H26C24.8954 23 24 23.8954 24 25V31C24 32.1046 24.8954 33 26 33H32C33.1046 33 34 32.1046 34 31V25C34 23.8954 33.1046 23 32 23Z"
            stroke="#404040" />
        </svg>
        <p class="text-base text-gray-700 font-medium">No file selected</p>
        <p class="text-sm text-gray-600">
          Select a file to get more information
        </p>
      </div>
    </div>
  </Transition>

  <div
    class="flex flex-col items-center h-full overflow-y-hidden border-l z-0 max-w-[50px] min-w-[50px] p-2 bg-white">
    <Button
      class="mb-2 py-4 text-gray-600"
      :class="[
        tab === 0 && showInfoSidebar
          ? 'text-black bg-gray-100'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(0)">
      <FeatherIcon
        name="alert-circle"
        :class="[
          tab === 0 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="text-gray-600 w-full h-full stroke-2" />
    </Button>
    <Button
      class="text-gray-600 py-4"
      :class="[
        tab === 1 && showInfoSidebar
          ? 'text-black bg-gray-100'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(1)">
      <FeatherIcon
        name="message-circle"
        :class="[
          tab === 1 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="text-gray-600 w-full h-full stroke-2" />
    </Button>
  </div>

  <ShareDialog
    v-if="showShareDialog && entity"
    v-model="showShareDialog"
    :entity-name="entity.name" />
</template>

<script>
import { FeatherIcon, Avatar, call, Input } from "frappe-ui";
import ShareDialog from "@/components/ShareDialog.vue";
import TagInput from "@/components/TagInput.vue";
import Tag from "@/components/Tag.vue";
import FileRender from "@/components/FileRender.vue";
import { formatMimeType, formatDate } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";

export default {
  name: "InfoSidebar",
  components: {
    Input,
    FeatherIcon,
    Avatar,
    ShareDialog,
    TagInput,
    Tag,
    FileRender,
  },

  /*   props: {
    entity: {
      type: Object,
      required: true,
    },
  }, */

  setup() {
    return { formatMimeType, getIconUrl };
  },

  data() {
    return {
      tab: 0,
      newComment: "",
      showShareDialog: false,
      addTag: false,
    };
  },

  watch: {
    entity: {
      handler() {
        if (this.entity) {
          this.$resources.comments.fetch();
          this.$resources.userTags.fetch();
          this.$resources.entityTags.fetch();
        }
      },
    },
  },

  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
    entity() {
      return this.$store.state.entityInfo;
    },
    formattedMimeType() {
      if (this.entity.is_group) return "Folder";
      const file = formatMimeType(this.entity.mime_type);
      return file.charAt(0).toUpperCase() + file.slice(1);
    },
    unaddedTags() {
      return this.$resources.userTags.data.filter(
        ({ name: id1 }) =>
          !this.$resources.entityTags.data.some(({ name: id2 }) => id2 === id1)
      );
    },
    showInfoSidebar() {
      return this.$store.state.showInfo;
    },
  },

  methods: {
    switchTab(val) {
      if (this.$store.state.showInfo == false) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
        this.tab = val;
      } else if (this.tab == val) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
      } else {
        this.tab = val;
      }
    },

    async postComment() {
      if (this.newComment.length) {
        try {
          await call("frappe.desk.form.utils.add_comment", {
            reference_doctype: "Drive Entity",
            reference_name: this.entity.name,
            content: this.newComment,
            comment_email: this.userId,
            comment_by: this.fullName,
          });
          this.newComment = "";
          this.$resources.comments.fetch();
        } catch (e) {
          console.log(e);
        }
      }
    },
  },

  resources: {
    comments() {
      return {
        url: "drive.api.files.list_entity_comments",
        params: { entity_name: this.entity?.name },
        onSuccess(data) {
          data.forEach((comment) => {
            comment.creation = formatDate(comment.creation);
          });
        },
        onError(error) {
          console.log(error);
        },
        auto: false,
      };
    },
    userTags() {
      return {
        url: "drive.api.tags.get_user_tags",
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
        auto: false,
      };
    },
    entityTags() {
      return {
        url: "drive.api.tags.get_entity_tags",
        params: { entity: this.entity?.name },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
        auto: false,
      };
    },
  },
};
</script>
