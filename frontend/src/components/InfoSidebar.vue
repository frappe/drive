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
              {{ store.state.entityInfo.length }} items selected
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="entity">
        <div class="w-full pl-3 py-4 border-b overflow-visible">
          <div class="flex items-center">
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
                (entity.mime_type?.startsWith('image') &&
                  entity?.mime_type !== 'image/svg+xml')) &&
              showInfoSidebar
            "
            class="relative p-0.5 aspect-video object-contain m-auto w-full flex items-center justify-center">
            <img class="h-auto max-h-full w-auto" :src="thumbnailLink" />
          </div>
          <div class="p-4 space-y-6">
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

            <div v-if="entity.owner === 'Me' || entityTags.data?.length">
              <div class="text-base font-medium mb-2">Tags</div>
              <div class="flex flex-wrap gap-2">
                <Tag
                  v-for="tag in entityTags?.data"
                  :key="tag"
                  :tag="tag"
                  :entity="entity"
                  @success="
                    () => {
                      userTags.fetch();
                      entityTags.fetch();
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
                :class="{ 'w-full': entityTags.data?.length }"
                :entity="entity"
                :unadded-tags="unaddedTags"
                @success="
                  () => {
                    userTags.fetch();
                    entityTags.fetch();
                    addTag = false;
                  }
                "
                @close="addTag = false" />
            </div>
            <div>
              <div class="text-base font-medium mb-2">Properties</div>
              <div class="flex text-sm justify-between">
                <div class="text-gray-600 space-y-1.5">
                  <div>Type</div>
                  <div v-if="entity.file_size">Size</div>
                  <div>Modified</div>
                  <div>Created</div>
                  <div>Owner</div>
                </div>
                <div class="text-right space-y-1.5">
                  <div>{{ formattedMimeType }}</div>
                  <div>{{ entity.file_size }}</div>
                  <div>{{ entity.modified }}</div>
                  <div>{{ entity.creation }}</div>
                  <div class="flex items-center">
                    <Avatar
                      :image="entity.user_image"
                      :label="entity.full_name"
                      class="relative mr-2"
                      size="sm" />
                    <span>{{ entity.full_name }}</span>
                  </div>
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
              v-for="comment in comments.data"
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
    class="hidden sm:flex flex-col items-center h-full overflow-y-hidden border-l z-0 max-w-[50px] min-w-[50px] p-2 bg-white">
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
      v-if="showComments"
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

<script setup>
import {
  ref,
  computed,
  onMounted,
  defineProps,
  onBeforeUnmount,
  watch,
} from "vue";
import { useStore } from "vuex";
import {
  FeatherIcon,
  Avatar,
  call,
  Input,
  Badge,
  createResource,
} from "frappe-ui";
import ShareDialog from "@/components/ShareDialog.vue";
import TagInput from "@/components/TagInput.vue";
import Tag from "@/components/Tag.vue";
import { formatMimeType, formatDate } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";
import { thumbnail_getIconUrl } from "@/utils/getIconUrl";

const store = useStore();
const tab = ref(0);
const newComment = ref("");
const showShareDialog = ref(false);
const addTag = ref(false);
const thumbnailLink = ref("");

const userId = computed(() => {
  return store.state.auth.user_id;
});

const fullName = computed(() => {
  return store.state.auth.user_id;
});

const imageURL = computed(() => {
  return store.state.user.imageURL;
});

const showInfoSidebar = computed(() => {
  return store.state.showInfo;
});

const formattedMimeType = computed(() => {
  if (entity.value.is_group) return "Folder";
  const file = formatMimeType(entity.value.mime_type);
  return file.charAt(0).toUpperCase() + file.slice(1);
});

const unaddedTags = computed(() => {
  return userTags.data.filter(
    ({ name: id1 }) => !entityTags.data.some(({ name: id2 }) => id2 === id1)
  );
});

const entity = computed(() => {
  if (store.state.entityInfo && store.state.entityInfo.length > 1) {
    return store.state.entityInfo.length;
  } else if (store.state.entityInfo?.length) {
    return store.state.entityInfo[0];
  } else if (store.state.currentFolder?.length) {
    return store.state.currentFolder[0];
  } else {
    return false;
  }
});

const showComments = computed(() => {
  if (entity.value.owner === "Me") {
    return true;
  } else if (entity.value.write) {
    return true;
  } else if (entity.value.allow_comments) {
    return true;
  } else {
    return false;
  }
});

function switchTab(val) {
  if (store.state.showInfo == false) {
    store.commit("setShowInfo", !store.state.showInfo);
    tab.value = val;
  } else if (tab.value == val) {
    store.commit("setShowInfo", !store.state.showInfo);
  } else {
    tab.value = val;
  }
}

async function thumbnailUrl() {
  let result = await thumbnail_getIconUrl(
    formatMimeType(entity.value.mime_type),
    entity.value.name,
    entity.value.file_ext
  );
  thumbnailLink.value = result;
}

watch(
  [entity, showInfoSidebar],
  ([newEntity, newShowInfoSidebar], [oldEntity, oldShowInfoSidebar]) => {
    if (
      newEntity &&
      typeof newEntity !== "number" &&
      typeof newEntity !== "undefined"
    ) {
      if (newShowInfoSidebar == true) {
        thumbnailUrl();
        comments.fetch({ entity_name: newEntity.name });
        entityTags.fetch({ entity: newEntity.name });
        userTags.fetch();
      }
    }
  }
);

async function postComment() {
  if (newComment.value.length) {
    try {
      await call("frappe.desk.form.utils.add_comment", {
        reference_doctype: "Drive Entity",
        reference_name: entity.value.name,
        content: newComment.value,
        comment_email: userId.value,
        comment_by: fullName.value,
      });
      newComment.value = "";
      comments.fetch();
    } catch (e) {
      console.log(e);
    }
  }
}

let comments = createResource({
  url: "drive.api.files.list_entity_comments",
  onSuccess(data) {
    data.forEach((comment) => {
      comment.creation = formatDate(comment.creation);
    });
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages);
    }
  },
  auto: false,
});

let userTags = createResource({
  url: "drive.api.tags.get_user_tags",
  onError(error) {
    if (error.messages) {
      console.log(error.messages);
    }
  },
  auto: false,
});

let entityTags = createResource({
  url: "drive.api.tags.get_entity_tags",
  onError(error) {
    if (error.messages) {
      console.log(error.messages);
    }
  },
  auto: false,
});
</script>
<style scoped>
.animate:active {
  transform: scaleX(0.985) scaleY(0.985) translateY(0.5px);
}
</style>
