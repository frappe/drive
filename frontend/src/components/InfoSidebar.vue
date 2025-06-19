<template>
  <div
    v-if="entity && store.state.showInfo"
    class="transition-all duration-200 ease-in-out h-full border-l sm:min-w-[352px] sm:max-w-[452px] shrink-0 whitespace-nowrap"
  >
    <div>
      <!-- Information -->
      <div
        v-if="tab === 0"
        class="h-full border-b px-5 pt-4 pb-5 w-full"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          {{ __("Information") }}
        </span>
        <div
          v-if="thumbnailUrl[2]"
          class="h-[210px] w-full mb-4"
        >
          <img
            class="object-contain h-full mx-auto"
            :src="thumbnailUrl[0] || thumbnailUrl[1]"
          />
        </div>
        <div class="space-y-6.5">
          <div v-if="entity.owner === $store.state.user.id">
            <div class="text-base font-medium mb-4">Access</div>
            <div class="flex items-center justify-between text-ink-gray-6">
              <div class="flex">
                <GeneralAccess
                  size="md"
                  class="-mr-[3px] outline outline-white"
                  :access-type="
                    generalAccess?.data?.read === 1 ? 'public' : 'restricted'
                  "
                />
                <div
                  v-if="userList.data?.length"
                  class="flex items-center justify-start ms-3"
                >
                  <Avatar
                    v-for="user in userList.data.slice(0, 3)"
                    :key="user?.user_name"
                    size="sm"
                    :label="user.full_name || user.user"
                    :image="user?.user_image"
                    class="-mr-[3px] outline outline-white"
                  />
                  <span
                    v-if="userList.data.slice(3).length"
                    class="text-base text-ink-gray-7 ms-1"
                  >
                    +{{ userList.data.slice(3).length }}
                  </span>
                </div>
              </div>
              <Button
                v-if="$store.state.activeEntity?.share"
                :variant="'subtle'"
                class="rounded flex justify-center items-center"
                @click="emitter.emit('showShareDialog')"
              >
                {{ __("Manage") }}
              </Button>
            </div>
          </div>
          <div v-if="userId !== 'Guest'">
            <div class="text-base font-medium mb-4 text-ink-gray-8">
              {{ __("Tags") }}
            </div>
            <TagInput
              class="min-w-full"
              :entity="entity"
            />
          </div>
          <div>
            <div class="text-base font-medium mb-4 text-ink-gray-8">
              {{ __("Properties") }}
            </div>
            <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
              <span class="col-span-1 text-ink-gray-5">{{ __("Type") }}</span>
              <span
                class="col-span-1 text-ink-gray-8"
                :title="entity.mime_type"
              >
                {{ entity.file_type }}
              </span>
              <span
                v-if="entity.file_size"
                class="col-span-1 text-ink-gray-5"
              >
                {{ __("Size") }}
              </span>
              <span
                v-if="entity.file_size"
                class="col-span-1 text-ink-gray-8"
              >
                {{ entity.file_size_pretty }}
                {{ `(${entity.file_size})` }}
              </span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Modified")
              }}</span>
              <span class="col-span-1 text-ink-gray-8">{{
                formatDate(entity.modified)
              }}</span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Uploaded")
              }}</span>
              <span class="col-span-1 text-ink-gray-8">{{
                formatDate(entity.creation)
              }}</span>
              <span class="col-span-1 text-ink-gray-5">{{ __("Owner") }}</span>
              <span class="col-span-1 text-ink-gray-8">{{
                entity.owner +
                (entity.owner === $store.state.user.id ? " (you)" : "")
              }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Comments -->
      <div
        v-if="entity.comment && tab === 1"
        class="max-h-[90vh] pt-4 pb-5 border-b overflow-y-auto overflow-x-hidden"
      >
        <span
          class="inline-flex items-center gap-2.5 px-5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          {{ __("Comments") }}
        </span>
        <!-- Check commenting permissions -->
        <div class="pb-2 px-5">
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
                <div
                  class="flex items-center justify-start text-base gap-x-1 text-ink-gray-5"
                >
                  <span class="font-medium text-ink-gray-8">{{
                    comment.comment_by
                  }}</span>
                  <span>∙ {{ comment.creation }}</span>
                </div>
                <span
                  class="my-2 text-base text-ink-gray-7 break-word leading-snug"
                >
                  {{ comment.content }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-start py-2">
            <Avatar
              :label="fullName"
              :image="imageURL"
              class="mr-3"
            />
            <div
              class="flex items-center border w-full bg-transparent rounded mr-1 focus-within:ring-2 ring-outline-gray-3 hover:bg-surface-gray-2 focus-within:bg-surface-gray-2 group"
            >
              <textarea
                v-model="newComment"
                class="disabled w-full form-textarea bg-transparent resize-none border-none hover:bg-transparent focus:ring-0 focus:shadow-none focus:bg-transparent"
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
              />
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="entity.write && tab === 2"
        class="max-h-[90vh] pt-4 pb-5 border-b overflow-y-auto overflow-x-hidden"
      >
        <span
          class="inline-flex items-center gap-2.5 px-5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          {{ __("Activity") }}
        </span>
        <ActivityTree
          v-if="entity.write"
          :entity="entity"
        />
      </div>
    </div>
  </div>

  <div
    class="hidden sm:flex flex-col items-center overflow-hidden h-full min-w-[48px] gap-1 pt-3 px-0 border-l z-0 bg-surface-white"
  >
    <Button
      class="text-ink-gray-5"
      :class="[
        tab === 0
          ? 'text-black bg-surface-gray-3'
          : ' hover:bg-surface-menu-bar',
      ]"
      variant="minimal"
      @click="switchTab(0)"
    >
      <LucideInfo class="size-4 text-ink-gray-6" />
    </Button>
    <Button
      v-if="entity?.comment"
      class="text-ink-gray-5"
      :class="[
        tab === 1
          ? 'text-black bg-surface-gray-3'
          : ' hover:bg-surface-menu-bar',
      ]"
      variant="minimal"
      @click="switchTab(1)"
    >
      <LucideMessageCircle class="size-4 text-ink-gray-6" />
    </Button>
    <Button
      v-if="entity?.write"
      class="text-ink-gray-5"
      :class="[
        tab === 2
          ? 'text-black bg-surface-gray-3'
          : ' hover:bg-surface-menu-bar',
      ]"
      variant="minimal"
      @click="switchTab(2)"
    >
      <LucideClock class="size-4 text-ink-gray-6" />
    </Button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue"
import { useStore } from "vuex"
import { Avatar, call, createResource } from "frappe-ui"
import { formatDate } from "@/utils/format"
import GeneralAccess from "@/components/GeneralAccess.vue"
import { getThumbnailUrl } from "@/utils/getIconUrl"
import ActivityTree from "./ActivityTree.vue"
import TagInput from "@/components/TagInput.vue"
import { generalAccess, userList } from "@/resources/permissions"
import LucideMessageCircle from "~icons/lucide/message-circle"

const store = useStore()
const tab = ref(0)
const newComment = ref("")

const userId = computed(() => store.state.user.id)
const fullName = computed(() => store.state.user.fullName)
const imageURL = computed(() => store.state.user.imageURL)
const entity = computed(() => store.state.activeEntity)
const thumbnailUrl = computed(() => {
  const res = getThumbnailUrl(entity.value?.name, entity.value?.file_type)
  console.log(res)
  return res
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

watch(entity, (newEntity) => {
  if (
    newEntity &&
    typeof newEntity !== "number" &&
    typeof newEntity !== "undefined"
  ) {
    if (
      (!newEntity.write && tab.value === 2) ||
      (!newEntity.comment && tab.value === 1)
    )
      tab.value = 0
    comments.fetch({ entity_name: newEntity.name })
    generalAccess.fetch({ entity: newEntity.name })
    userList.fetch({ entity: newEntity.name })
  }
})

async function postComment() {
  if (newComment.value.length) {
    try {
      await call("drive.utils.users.add_comment", {
        reference_doctype: "Drive File",
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

function resize(e) {
  e.target.style.height = `${e.target.scrollHeight}px`
}
</script>
