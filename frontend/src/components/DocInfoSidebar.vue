<template>
  <Transition
    enter-from-class="translate-x-[150%] opacity-0"
    leave-to-class="translate-x-[150%] opacity-0"
    enter-active-class="transition duration-125"
    leave-active-class="transition duration-125">
    <div
      v-if="showInfoSidebar"
      class="min-w-[300px] max-w-[300px] min-h-full border-l overflow-auto">
      <div v-if="entity" class="w-full border-b p-4">
        <div class="flex items-center">
          <svg
            width="20px"
            class="mr-2.5"
            height="20px"
            viewBox="0 0 14 14"
            fill="none"
            xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0 3C0 1.34315 1.34315 0 3 0H11C12.6569 0 14 1.34315 14 3V11C14 12.6569 12.6569 14 11 14H3C1.34315 14 0 12.6569 0 11V3Z"
              fill="#525252" />
            <path d="M3.5 4H10.5V5H3.5V4Z" fill="#FBFFFF" />
            <path d="M3.5 6.5H10.5V7.5H3.5V6.5Z" fill="#FBFFFF" />
            <path d="M3.5 9H8.5V10H3.5V9Z" fill="#FBFFFF" />
          </svg>
          <img :draggable="false" class="h-5 mr-2.5" />
          <div class="font-medium truncate text-xl">
            {{ entity.title }}
          </div>
        </div>
      </div>
      <!-- :class="$store.state.showInfo ? 'min-h-[45px]' : 'min-h-[48px]'" -->
      <!-- grow  min-h-full -->
      <div v-if="entity">
        <div class="flex flex-col justify-start">
          <div
            class="p-4 border-b"
            :class="
              tab === 0
                ? 'flex-auto'
                : 'text-gray-600 cursor-pointer flex-none '
            "
            @click="tab = 0">
            <span class="font-medium text-lg">Doc Info</span>
            <div
              v-if="tab === 0"
              class="space-y-7 min-h-full flex-auto flex flex-col z-0 overflow-y-auto">
              <div v-if="entity.owner === 'Me'">
                <div class="text-lg font-medium my-4">Manage Access</div>
                <div class="flex flex-row">
                  <Button class="h-7" @click="showShareDialog = true">
                    Share
                  </Button>
                </div>
              </div>
              <div
                v-if="
                  entity.owner === 'Me' || $resources.entityTags.data?.length
                ">
                <div class="text-lg font-medium mb-4">Tag</div>
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
                    v-if="!addTag && entity.owner === 'Me'"
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
              <div class="text-lg font-medium mb-4">Properties</div>
              <div class="flex text-base">
                <div class="w-1/2 text-gray-600 space-y-2">
                  <div>Type</div>
                  <div>Size</div>
                  <div>Modified</div>
                  <div>Created</div>
                  <div>Owner</div>
                </div>
                <div class="w-1/2 space-y-2">
                  <div>Frappe Doc</div>
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

          <!-- Figure out a way to fetch and store document comments to show here -->

          <span v-if="tab === 1" class="font-medium text-lg">Comments</span>
          <div
            v-if="tab === 1"
            class="p-4 border-b"
            :class="tab === 1 ? 'flex-auto' : 'text-gray-600 cursor-pointer'"
            @click="tab = 1"></div>
          <div v-if="tab === 1" class="h-full overflow-y-auto">
            <div v-if="entity.allow_comments" class="space-y-5">
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
              <div v-if="userId != 'Guest'" class="flex items-center gap-3">
                <Avatar :label="fullName" :image="imageURL" class="h-7 w-7" />
                <div class="flex">
                  <Input
                    v-model="newComment"
                    type="text"
                    class="border-gray-400 placeholder-gray-500 w-full grow bg-white focus:bg-white"
                    placeholder="Add comment"
                    @keydown.enter="postComment" />
                </div>
                <Button variant="solid" @click="postComment">Add</Button>
              </div>
            </div>
            <OuterCommentVue
              v-if="!!allComments.length"
              :active-comments-instance="activeCommentsInstance"
              :all-comments="allComments"
              @focus-content="triggerFocusContent"
              @set-comment="triggerSetContent" />
            <div v-else class="text-gray-600 text-base mt-2">
              There are no comments for the current document
            </div>
          </div>
        </div>
      </div>
      <div
        v-else
        class="flex h-full w-full flex-col items-center justify-center rounded-lg text-center">
        <svg viewBox="0 0 78 85" class="w-1/6 fill-transparent stroke-2 pb-6">
          <path
            d="M42 31H66 M42 51H66 M42 25H55 M42 45H55 M65 9V8C65 4.13401 61.866 1 58 1H8C4.13401 1 1 4.13401 1 8V66C1 69.866 4.13401 73 8 73H10 M70 12H20C16.134 12 13 15.134 13 19V77C13 80.866 16.134 84 20 84H70C73.866 84 77 80.866 77 77V19C77 15.134 73.866 12 70 12Z"
            stroke="#525252" />
          <path
            d="M32 43H26C24.8954 43 24 43.8954 24 45V51C24 52.1046 24.8954 53 26 53H32C33.1046 53 34 52.1046 34 51V45C34 43.8954 33.1046 43 32 43Z M32 23H26C24.8954 23 24 23.8954 24 25V31C24 32.1046 24.8954 33 26 33H32C33.1046 33 34 32.1046 34 31V25C34 23.8954 33.1046 23 32 23Z"
            stroke="#525252" />
        </svg>
        <p class="text-base text-gray-700 font-medium">No file selected</p>
        <p class="text-sm text-gray-600">
          Select a file to get more information
        </p>
      </div>
      <ShareDialog
        v-if="showShareDialog"
        v-model="showShareDialog"
        :entity-name="entity.name" />
    </div>
  </Transition>

  <div
    class="flex flex-col items-center h-full overflow-y-hidden z-0 border-l max-w-[50px] min-w-[50px] p-2 bg-white">
    <Button
      :class="[
        tab === 0 && showInfoSidebar
          ? 'text-black bg-gray-100'
          : ' hover:bg-gray-50',
      ]"
      class="mb-2 py-4 text-gray-600"
      variant="minimal"
      @click="switchTab(0)">
      <FeatherIcon
        name="alert-circle"
        :class="[
          tab === 0 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
    <Button
      v-if="$route.meta.documentPage"
      class="mb-2 text-gray-600 py-4"
      :class="[
        tab === 1 && showInfoSidebar
          ? 'text-black bg-gray-300'
          : ' hover:bg-gray-100',
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
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
  </div>
</template>

<script>
import { FeatherIcon, Avatar, Input } from "frappe-ui";
import ShareDialog from "@/components/ShareDialog.vue";
import TagInput from "@/components/TagInput.vue";
import Tag from "@/components/Tag.vue";
import OuterCommentVue from "@/components/DocEditor/OuterComment.vue";

export default {
  name: "DocInfoSidebar",
  components: {
    Input,
    FeatherIcon,
    Avatar,
    ShareDialog,
    TagInput,
    Tag,
    OuterCommentVue,
  },
  emits: ["setContentEmit", "focusContentEmit"],
  /* setup() {
    return { formatMimeType, getIconUrl };
  },
 */
  data() {
    return {
      tab: 0,
      newComment: "",
      showShareDialog: false,
      addTag: false,
    };
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
    unaddedTags() {
      return this.$resources.userTags.data.filter(
        ({ name: id1 }) =>
          !this.$resources.entityTags.data.some(({ name: id2 }) => id2 === id1)
      );
    },
    allComments() {
      console.log(this.$store.state.allComments);
      return JSON.parse(this.$store.state.allComments);
    },
    activeCommentsInstance() {
      return JSON.parse(this.$store.state.activeCommentsInstance);
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
    triggerSetContent(val) {
      this.emitter.emit("setContentEmit", val);
    },
    triggerFocusContent(val) {
      this.emitter.emit("focusContentEmit", val);
    },
    toggleSideBar() {
      if (this.entity) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
      }
    },
  },

  resources: {
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
