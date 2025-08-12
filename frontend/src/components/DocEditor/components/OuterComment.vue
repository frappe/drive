<template>
  <section class="text-sm w-full flex flex-col overflow-x-hidden min-w-full">
    <article
      v-for="(comment, i) in allComments"
      :key="i + ''"
      class="current-comment pt-2 bg-surface-white flex flex-col border-b last:border-b-0"
      :class="[
        `${
          comment.jsonComments.uuid === activeCommentsInstance.uuid
            ? 'active'
            : 'cursor-pointer'
        }`,
      ]"
      @click.stop.prevent="focusContent({ from: comment.from, to: comment.to })"
    >
      <div
        v-for="(jsonComment, j) in comment.jsonComments.comments"
        :key="`${j}_${Math.random()}`"
        class="flex items-start justify-start my-5"
      >
        <Avatar
          :label="jsonComment.userName"
          :image="jsonComment.userImage"
          class="h-7 w-7"
        />
        <div class="ml-3">
          <div class="flex items-center justify-start text-base gap-x-1">
            <span class="font-medium">
              {{ jsonComment.userName }}
            </span>
            <span class="text-ink-gray-4">{{ " ∙ " }}</span>
            <span class="text-ink-gray-5">
              {{ formatDate(jsonComment.time) }}
            </span>
          </div>
          <div
            class="my-2 text-base text-ink-gray-7 break-word leading-snug comment-content"
            v-html="renderCommentContent(jsonComment.content)"
          ></div>
        </div>
      </div>

      <section
        v-show="comment.jsonComments.uuid == activeCommentsInstance.uuid"
        class="flex flex-col"
        :class="[
          `${
            comment.jsonComments.uuid === activeCommentsInstance.uuid
              ? ''
              : 'max-h-0'
          }`,
        ]"
      >
        <div class="flex items-center gap-1 mt-2 mb-4">
          <Avatar
            :label="fullName"
            :image="imageURL"
            class="h-7 w-7 mr-1"
          />
          <div class="w-full max-w-[87%]">
            <RichCommentEditor
              ref="richEditor"
              v-model="commentText"
              :entity-name="entityName"
              placeholder="Add comment (use @ to mention users)"
              @mentioned-users="(val) => (mentionedUsers = val)"
            />
            <div class="flex justify-end mt-2">
              <Button
                variant="ghost"
                size="sm"
                icon="arrow-up-circle"
                :disabled="isCommentEmpty"
                @click="setComment"
              >
                Reply
              </Button>
            </div>
          </div>
        </div>
      </section>
    </article>
  </section>
</template>

<script setup lang="ts">
import { useStore } from "vuex"
import { ref, watch, computed, nextTick, onUpdated } from "vue"
import { Avatar, Button, Input } from "frappe-ui"
import { formatDate } from "@/utils/format"
import RichCommentEditor from "./RichCommentEditor.vue"

const store = useStore()

const emit = defineEmits(["setComment"])

interface Props {
  allComments: any[]
  activeCommentsInstance: {
    uuid: ""
    comments: []
  }
  isCommentModeOn: boolean
  entityName: string
  focusContent: ({ from, to }: { from: number; to: number }) => void
}

const props = defineProps<Props>()

const commentText = ref<string>("")
const mentionedUsers = ref<any[]>([])
const richEditor = ref<any>(null)

const textarea = ref<Record<string, any>>({})

const activeCommentInstanceUuid = computed(
  () => props.activeCommentsInstance.uuid
)

const fullName = computed(() => store.state.user.fullName)

const imageURL = computed(() => store.state.user.imageURL)

const isCommentEmpty = computed(() => {
  return !commentText.value || richEditor.value?.isEmpty()
})

const setComment = () => {
  if (isCommentEmpty.value) return
  emit("setComment", {
    content: commentText.value,
    mentions: mentionedUsers.value
  })
  commentText.value = ""
  mentionedUsers.value = []
  if (richEditor.value) {
    richEditor.value.clear()
  }
}

const renderCommentContent = (content: string) => {
  // If content is HTML (from rich editor), return as is
  if (content.includes('<') && content.includes('>')) {
    return content
  }
  // If content is plain text, return as is
  return content
}

watch(activeCommentInstanceUuid, (val) => {
  setTimeout(() => {
    if (!val || !props.isCommentModeOn) return
    commentText.value = ""
    mentionedUsers.value = []

    if (richEditor.value) {
      richEditor.value.clear()
      richEditor.value.focus()
    }
  }, 100)
})
</script>

<style lang="scss" scoped>
.current-comment {
  transition: all 2s cubic-bezier(0.165, 0.84, 0.44, 1);

  &.active {
    padding: 10px 0px;
  }
}

:deep(.comment-content span[data-type="mention"]) {
  background-color: rgba(59, 130, 246, 0.1) !important;
  color: #3b82f6 !important;
  border-radius: 4px;
  padding: 2px 4px;
  font-weight: 500;
  text-decoration: none;
}
</style>
