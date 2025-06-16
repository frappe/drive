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
          <span
            class="my-2 text-base text-ink-gray-7 break-word leading-snug"
            >{{ jsonComment.content }}</span
          >
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
          <div
            class="flex items-center mx-auto border w-full bg-transparent rounded max-w-[87%] focus-within:ring-2 ring-outline-gray-3 hover:bg-surface-gray-2 focus-within:bg-surface-gray-2 group"
          >
            <textarea
              v-model="commentText"
              class="w-full form-textarea bg-transparent resize-none border-none hover:bg-transparent focus:ring-0 focus:shadow-none focus:bg-transparent"
              placeholder="Add comment"
              @input="resize($event)"
              @keypress.enter.stop.prevent="setComment"
            />
            <Button
              class="hover:bg-transparent"
              variant="ghost"
              icon="arrow-up-circle"
              :disabled="!commentText.length"
              @click="setComment"
            ></Button>
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

const store = useStore()

const emit = defineEmits(["setComment"])

interface Props {
  allComments: any[]
  activeCommentsInstance: {
    uuid: ""
    comments: []
  }
  isCommentModeOn: boolean
  focusContent: ({ from, to }: { from: number; to: number }) => void
}

const props = defineProps<Props>()

const commentText = ref<string>("")

const textarea = ref<Record<string, any>>({})

const activeCommentInstanceUuid = computed(
  () => props.activeCommentsInstance.uuid
)

const fullName = computed(() => store.state.user.fullName)

const imageURL = computed(() => store.state.user.imageURL)

const setComment = () => {
  emit("setComment", commentText.value)
  commentText.value = ""
}

watch(activeCommentInstanceUuid, (val) => {
  setTimeout(() => {
    if (!val || !props.isCommentModeOn) return
    commentText.value = ""

    const activeTextArea: HTMLTextAreaElement = textarea.value[val]

    //if (activeTextArea) activeTextArea.focus()
  }, 100)
})

function resize(e) {
  e.target.style.height = `${e.target.scrollHeight}px`
}

/* watch(commentText, (val) => {
  nextTick(() => {
    console.log(textarea.value.style)
    //textarea.value.style.height = textarea.value.style.scrollHeight + 'px';
  })
}) */
</script>

<style lang="scss" scoped>
.current-comment {
  transition: all 2s cubic-bezier(0.165, 0.84, 0.44, 1);

  &.active {
    padding: 10px 0px;
  }
}
</style>
