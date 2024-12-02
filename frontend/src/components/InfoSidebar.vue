<template>
  <div
    class="transition-all duration-200 ease-in-out h-full border-l"
    :class="
      showInfoSidebar
        ? 'sm:min-w-[352px] sm:max-w-[352px] min-w-full opacity-100'
        : 'w-0 min-w-0 max-w-0 overflow-hidden opacity-0'
    "
  >
    <div v-if="typeof entity === 'number'">
      <div class="w-full px-5 py-4 border-b overflow-visible">
        <div class="flex items-center">
          <div class="font-medium truncate text-lg">
            {{ store.state.entityInfo.length }} items selected
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="entity">
      <div class="w-full px-5 py-4 border-b">
        <div class="flex items-center">
          <div class="font-medium truncate text-lg">
            {{ entity.title }}
          </div>
          <Button
            icon="x"
            variant="ghost"
            class="ml-auto sm:hidden"
            @click="$store.commit('setShowInfo', false)"
          />
        </div>
      </div>
      <!-- Information -->
      <div v-if="tab === 0" class="h-full border-b px-5 pt-4 pb-5 w-full">
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
        >
          <!-- <Info /> -->
          Information
        </span>
        <div
          v-if="
            (entity.mime_type?.startsWith('video') ||
              (entity.mime_type?.startsWith('image') &&
                entity?.mime_type !== 'image/svg+xml')) &&
            showInfoSidebar
          "
          class="h-[210px] w-full mb-4"
        >
          <img class="object-contain h-full mx-auto" :src="thumbnailLink" />
        </div>
        <div class="space-y-6.5">
          <div v-if="entity.owner === 'You'">
            <div class="text-base font-medium mb-4">Access</div>
            <div class="flex items-center justify-start">
              <Avatar
                size="md"
                :label="entity.owner"
                :image="entity.user_image"
              />
              <div class="border-l h-6 mx-1.5"></div>
              <GeneralAccess
                v-if="
                  !generalAccess.loading &&
                  (!!generalAccess.data?.length || !sharedWithList?.length)
                "
                size="md"
                class="-mr-[3px] outline outline-white"
                :general-access="generalAccess?.data?.[0]"
              />
              <div
                v-if="sharedWithList?.length && !sharedWithList.loading"
                class="flex items-center justify-start"
              >
                <Avatar
                  v-for="user in sharedWithList.slice(0, 3)"
                  :key="user?.user_name"
                  size="md"
                  :label="user?.full_name ? user?.full_name : user?.user_name"
                  :image="user?.user_image"
                  class="-mr-[3px] outline outline-white"
                />

                <Avatar
                  v-if="sharedWithList.slice(3).length"
                  size="md"
                  :label="sharedWithList.slice(3).length.toString()"
                  class="-mr-[3px] outline outline-white"
                />
              </div>
            </div>
          </div>
          <div v-if="userId !== 'Guest'">
            <div class="text-base font-medium mb-4">Tags</div>
            <TagInput class="min-w-full" :entity="entity" />
          </div>
          <div>
            <div class="text-base font-medium mb-4">Properties</div>
            <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
              <span class="col-span-1 text-gray-600">Type</span>
              <span class="col-span-1">{{ formattedMimeType }}</span>
              <span v-if="entity.file_size" class="col-span-1 text-gray-600">
                Size
              </span>
              <span v-if="entity.file_size" class="col-span-1">
                {{ entity.file_size }}
              </span>
              <span class="col-span-1 text-gray-600">Modified</span>
              <span class="col-span-1">{{ entity.modified }}</span>
              <span class="col-span-1 text-gray-600">Uploaded</span>
              <span class="col-span-1">{{ entity.creation }}</span>
              <span class="col-span-1 text-gray-600">Owner</span>
              <span class="col-span-1">{{ entity.full_name }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Comments -->
      <div
        v-if="tab === 1"
        class="max-h-[90vh] pt-4 pb-5 border-b overflow-y-auto overflow-x-hidden"
      >
        <span
          class="inline-flex items-center gap-2.5 px-5 mb-5 text-gray-800 font-medium text-lg w-full"
        >
          <!--  <Comment /> -->
          Comments
        </span>
        <div v-if="entity.allow_comments" class="pb-2 px-5">
          <div
            v-for="comment in comments.data"
            :key="comment"
            class="flex flex-col mb-5"
          >
            <div class="flex items-start justify-start">
              <Avatar
                :label="comment.comment_by"
                :image="comment.user_image"
                size="md"
              />
              <div class="ml-3">
                <div class="flex items-center justify-start text-base gap-x-1">
                  <span class="font-medium">{{ comment.comment_by }}</span>
                  <span>{{ "∙" }}</span>
                  <span class="text-gray-600">{{ comment.creation }}</span>
                </div>
                <span
                  class="my-2 text-base text-gray-700 break-word leading-snug"
                >
                  {{ comment.content }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-start py-2">
            <Avatar :label="fullName" :image="imageURL" class="mr-3" />
            <div
              class="flex items-center border w-full bg-transparent rounded mr-1 focus-within:ring-2 ring-gray-400 hover:bg-gray-100 focus-within:bg-gray-100 group"
            >
              <textarea
                v-model="newComment"
                class="w-full form-textarea bg-transparent resize-none border-none hover:bg-transparent focus:ring-0 focus:shadow-none focus:bg-transparent"
                placeholder="Add a comment"
                @input="resize($event)"
                @keypress.enter.stop.prevent="postComment"
              />
              <Button
                class="hover:bg-transparent"
                variant="ghost"
                icon="arrow-up-circle"
                :disabled="!newComment.length"
                @click="postComment"
              ></Button>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-600 text-sm px-5">
          Comments have been disabled for this
          {{ entity.is_group ? "folder" : "file" }} by its owner.
        </div>
      </div>
      <div
        v-if="tab === 2 && userId !== 'Guest'"
        class="max-h-[90vh] pt-4 pb-5 border-b overflow-y-auto overflow-x-hidden"
      >
        <span
          class="inline-flex items-center gap-2.5 px-5 mb-5 text-gray-800 font-medium text-lg w-full"
        >
          <!-- <Clock /> -->
          Activity
        </span>
        <ActivityTree v-if="showActivity" />
      </div>
    </div>
    <div
      v-else
      class="flex h-full w-full flex-col items-center justify-center rounded-lg text-center"
    >
      <File class="w-auto h-10 text-gray-600 mb-2" />
      <p class="text-sm text-gray-600 font-medium">No file selected</p>
    </div>
  </div>

  <div
    class="hidden sm:flex flex-col items-center overflow-hidden h-full min-w-[48px] gap-1 pt-3 px-0 border-l z-0 bg-white"
  >
    <Button
      class="text-gray-600"
      :class="[
        tab === 0 && showInfoSidebar
          ? 'text-black bg-gray-200'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(0)"
    >
      <Info />
    </Button>
    <Button
      v-if="showComments"
      class="text-gray-600"
      :class="[
        tab === 1 && showInfoSidebar
          ? 'text-black bg-gray-200'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(1)"
    >
      <Comment />
    </Button>
    <Button
      v-if="showActivity && userId !== 'Guest'"
      class="text-gray-600"
      :class="[
        tab === 2 && showInfoSidebar
          ? 'text-black bg-gray-200'
          : ' hover:bg-gray-50',
      ]"
      variant="minimal"
      @click="switchTab(2)"
    >
      <Clock />
    </Button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue"
import { useStore } from "vuex"
import { Avatar, call, createResource } from "frappe-ui"
import { formatMimeType, formatDate } from "@/utils/format"
import GeneralAccess from "@/components/GeneralAccess.vue"
import { thumbnail_getIconUrl } from "@/utils/getIconUrl"
import Info from "./EspressoIcons/Info.vue"
import File from "./EspressoIcons/File.vue"
import Comment from "./EspressoIcons/Comment.vue"
import Clock from "./EspressoIcons/Clock.vue"
import ActivityTree from "./ActivityTree.vue"
import Tag from "@/components/Tag.vue"
import TagInput from "@/components/TagInput.vue"
const store = useStore()
const tab = ref(0)
const addTag = ref(false)
const newComment = ref("")
const thumbnailLink = ref("")

const userId = computed(() => {
  return store.state.auth.user_id
})

const fullName = computed(() => {
  return store.state.user.fullName
})

const imageURL = computed(() => {
  return store.state.user.imageURL
})

const showInfoSidebar = computed(() => {
  return store.state.showInfo
})

const formattedMimeType = computed(() => {
  if (entity.value.is_group) return "Folder"
  const file = entity.value.file_kind
  return file?.charAt(0).toUpperCase() + file?.slice(1)
})

const entity = computed(() => {
  if (store.state.entityInfo && store.state.entityInfo.length > 1) {
    return store.state.entityInfo.length
  } else if (store.state.entityInfo?.length) {
    return store.state.entityInfo[0]
  } else if (store.state.currentFolder?.length) {
    return store.state.currentFolder[0]
  } else {
    return false
  }
})

const sharedWithList = computed(() => {
  return userList.data?.users.concat(groupList.data)
})

const showComments = computed(() => {
  if (entity.value.owner === "You") {
    return true
  } else if (entity.value.write) {
    return true
  } else if (entity.value.allow_comments) {
    return true
  } else {
    return false
  }
})

const showActivity = computed(() => {
  if (entity.value.owner === "You") {
    return true
  } else if (entity.value.write) {
    return true
  }
  return false
})

function switchTab(val) {
  if (store.state.showInfo == false) {
    store.commit("setShowInfo", !store.state.showInfo)
    tab.value = val
  } else if (tab.value == val) {
    store.commit("setShowInfo", !store.state.showInfo)
  } else {
    tab.value = val
  }
}

async function thumbnailUrl() {
  let result = await thumbnail_getIconUrl(
    formatMimeType(entity.value.mime_type),
    entity.value.name,
    entity.value.file_ext
  )
  thumbnailLink.value = result
}

watch([entity, showInfoSidebar], ([newEntity, newShowInfoSidebar]) => {
  if (
    newEntity &&
    typeof newEntity !== "number" &&
    typeof newEntity !== "undefined"
  ) {
    if (newShowInfoSidebar == true) {
      thumbnailUrl()
      comments.fetch({ entity_name: newEntity.name })
      if (userId.value === "Guest") return
      generalAccess.fetch({ entity_name: newEntity.name })
      userList.fetch({ entity_name: newEntity.name })
      groupList.fetch({ entity_name: newEntity.name })
    }
  }
})

async function postComment() {
  if (newComment.value.length) {
    try {
      await call("drive.utils.users.add_comment", {
        reference_doctype: "Drive Entity",
        reference_name: entity.value.name,
        content: newComment.value,
        comment_email: userId.value,
        comment_by: fullName.value,
      })
      newComment.value = ""
      comments.fetch()
    } catch (e) {
      console.log(e)
    }
  }
}

let comments = createResource({
  url: "drive.api.files.list_entity_comments",
  onSuccess(data) {
    data.forEach((comment) => {
      comment.creation = formatDate(comment.creation)
    })
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages)
    }
  },
  auto: false,
})

const generalAccess = createResource({
  url: "drive.api.permissions.get_general_access",
  auto: false,
})

const userList = createResource({
  url: "drive.api.permissions.get_shared_with_list",
  auto: false,
})

const groupList = createResource({
  url: "drive.api.permissions.get_shared_user_group_list",
  auto: false,
})

function resize(e) {
  e.target.style.height = `${e.target.scrollHeight}px`
}
</script>
