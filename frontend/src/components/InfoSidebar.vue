<template>
  <Transition
    enter-from-class="translate-x-[150%] opacity-0"
    leave-to-class="translate-x-[150%] opacity-0"
    enter-active-class="transition duration-125"
    leave-active-class="transition duration-125">
    <div
      v-if="showInfoSidebar"
      class="min-w-[300px] max-w-[300px] min-h-full border-l overflow-auto">
      <div v-if="typeof entity === 'number'">
        <div class="w-full p-4 border-b overflow-visible">
          <div class="flex items-center">
            <div class="font-medium truncate text-lg">
              {{ $store.state.entityInfo.length }} items selected
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="entity">
        <div class="w-full p-4 border-b overflow-visible">
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
            <div class="font-medium truncate text-lg">
              {{ entity.title }}
            </div>
          </div>
        </div>
        <div v-if="tab === 0" class="h-full border-b">
          <!--           <div
            class="p-4 z-10 sticky top-0 bg-white"
            :class="
              tab === 0
                ? 'flex-auto'
                : 'text-gray-600 cursor-pointer flex-none '
            "
            @click="tab = 0">
            <div class="flex items-center">
              <FeatherIcon name="alert-circle" class="h-4 mr-2 stroke-2" />
              <span class="font-medium text-lg">Information</span>
            </div>
          </div> -->
          <div
            v-if="
              (entity.mime_type?.startsWith('video') ||
                entity.mime_type?.startsWith('image')) &&
              showInfoSidebar
            "
            class="relative p-4 min-h-full flex-auto flex flex-col overflow-y-auto">
            <img :src="thumbnailLink" />
          </div>
          <div class="p-4 space-y-8">
            <div v-if="entity.owner === 'Me'">
              <div class="text-base font-medium mb-2">Manage Access</div>
              <div class="flex flex-row">
                <Button
                  icon-left="share-2"
                  class="h-7"
                  @click="showShareDialog = true">
                  Share
                </Button>
              </div>
            </div>

            <div
              v-if="
                entity.owner === 'Me' || $resources.entityTags.data?.length
              ">
              <div class="text-base font-medium mb-2">Tags</div>
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
                <Badge
                  v-if="!addTag && entity.owner === 'Me'"
                  class="flex items-center content-center cursor-pointer font-medium"
                  @click="addTag = true">
                  <FeatherIcon
                    v-if="entity.owner === 'Me'"
                    class="h-3 stroke-2"
                    name="plus" />
                  Add tag
                </Badge>
              </div>

              <TagInput
                v-if="addTag"
                :class="{ 'w-full': $resources.entityTags.data.length }"
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
            <div>
              <div class="text-base font-medium mb-2">Properties</div>
              <div class="flex text-base">
                <div class="w-1/2 text-gray-600 space-y-2">
                  <div>Type</div>
                  <div v-if="entity.file_size">Size</div>
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
            </div>
          </div>
        </div>
        <div v-if="tab === 1" class="h-full pb-12">
          <div class="flex items-center pl-4 pt-4 sticky top-0 bg-white">
            <span class="font-medium text-base mb-2">Comments</span>
          </div>
          <div
            v-if="entity.allow_comments"
            class="px-4 overflow-y-auto pb-4 space-y-6">
            <div
              v-for="comment in $resources.comments.data"
              :key="comment"
              class="flex gap-3 items-center">
              <Avatar
                :label="comment.comment_by"
                :image="comment.user_image"
                class="h-7 w-7" />
              <div>
                <span class="text-sm font-medium">
                  {{ comment.comment_by }}
                </span>
                <span class="text-gray-500 text-sm">{{ " ∙ " }}</span>
                <span class="text-gray-700 text-sm">
                  {{ comment.creation }}
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
          <div v-else class="text-gray-600 text-sm p-4 border-b">
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
      class="animate mb-2 py-4 text-gray-600"
      :class="[
        tab === 0 && showInfoSidebar
          ? 'text-black bg-gray-200'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(0)">
      <FeatherIcon
        name="info"
        :class="[
          tab === 0 && showInfoSidebar ? 'text-gray-700' : 'text-gray-600',
        ]"
        class="text-gray-600 w-full h-full stroke-1.5" />
    </Button>
    <Button
      class="animate mb-2 text-gray-600 py-4"
      :class="[
        tab === 1 && showInfoSidebar
          ? 'text-black bg-gray-200'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(1)">
      <FeatherIcon
        name="message-circle"
        :class="[
          tab === 1 && showInfoSidebar ? 'text-gray-700' : 'text-gray-600',
        ]"
        class="text-gray-600 w-full h-full stroke-1.5" />
    </Button>
  </div>

  <ShareDialog
    v-if="showShareDialog && entity"
    v-model="showShareDialog"
    :entity-name="entity.name" />
</template>

<script>
import { FeatherIcon, Avatar, call, Input, Badge } from "frappe-ui";
import ShareDialog from "@/components/ShareDialog.vue";
import TagInput from "@/components/TagInput.vue";
import Tag from "@/components/Tag.vue";
import { formatMimeType, formatDate } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";
import File from "@/components/File.vue";
import { thumbnail_getIconUrl } from "@/utils/getIconUrl";

export default {
  name: "InfoSidebar",
  components: {
    Input,
    FeatherIcon,
    Avatar,
    ShareDialog,
    TagInput,
    Tag,
    Badge,
    File,
  },

  setup() {
    return { formatMimeType, getIconUrl };
  },

  data() {
    return {
      tab: 0,
      newComment: "",
      showShareDialog: false,
      addTag: false,
      thumbnailLink: "",
    };
  },
  watch: {
    entity: {
      handler(newVal, oldVal) {
        if (this.showInfoSidebar) {
          if (
            newVal !== oldVal &&
            typeof newVal !== "number" &&
            typeof newVal !== "undefined"
          ) {
            this.thumbnailUrl();
            this.$resources.comments.fetch();
            this.$resources.userTags.fetch();
            this.$resources.entityTags.fetch();
          }
        }
      },
    },
    showInfoSidebar: {
      handler(newVal, oldVal) {
        if (
          newVal !== oldVal &&
          typeof newVal !== "number" &&
          typeof newVal !== "undefined"
        ) {
          this.thumbnailUrl();
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
      if (
        this.$store.state.entityInfo &&
        this.$store.state.entityInfo.length > 1
      ) {
        return this.$store.state.entityInfo.length;
      } else if (this.$store.state.entityInfo) {
        return this.$store.state.entityInfo[0];
      } else {
        return false;
      }
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

    async thumbnailUrl() {
      let result = await thumbnail_getIconUrl(
        formatMimeType(this.entity.mime_type),
        this.entity.name,
        this.file_ext
      );
      this.thumbnailLink = result;
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
<style scoped>
.animate:active {
  transform: scaleX(0.985) scaleY(0.985) translateY(0.5px);
}
</style>
