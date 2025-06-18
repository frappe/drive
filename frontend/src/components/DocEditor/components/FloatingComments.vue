<template>
  <div
    ref="comments-section"
    class="border-s-2 py-4 px-12 flex flex-col gap-8 justify-start max-h-full overflow-auto"
  >
    <div
      v-for="comment in formattedComments"
      :key="comment.name"
      :id="'comment-' + comment.name"
      @click="activeComment = comment.name"
      class="rounded border w-52 comment-group shadow-sm"
      :class="activeComment === comment.name && 'border-yellow-300 shadow-2xl'"
    >
      <div
        v-show="activeComment === comment.name"
        class="px-2 py-1 text-sm flex gap-1 border-b text-ink-gray-9"
      >
        <Button
          variant="ghost"
          size="xs"
        >
          <template #prefix>
            <LucideCheck class="size-3.5" />
          </template>
          Resolve
        </Button>
        <Button
          variant="ghost"
          size="xs"
        >
          <template #prefix>
            <LucideX class="size-3.5" />
          </template>
          Delete
        </Button>
      </div>
      <div class="px-3 py-2.5 flex gap-2 text-ink-gray-9">
        <Avatar
          :label="comment.owner"
          :image="comment.image"
        />
        <div>
          <div class="label-group flex gap-1 text-sm items-start">
            <label class="font-medium text-ink-gray-8">{{
              comment.full_name
            }}</label>
            <span class="text-ink-gray-7">{{ " ∙ " }}</span>
            <label class="text-ink-gray-6">{{ comment.created_on }}</label>
          </div>
          <div class="comment-content text-sm mt-1">
            {{ comment.content }}

            <div
              v-show="activeComment === comment.name"
              class="flex gap-1 mt-2"
            >
              <Button
                variant="subtle"
                size="xs"
                class="font-medium"
              >
                Edit
              </Button>
              <Button
                variant="subtle"
                size="xs"
                class="font-medium"
                >Delete</Button
              >
            </div>
          </div>
        </div>
      </div>
      <div class="pb-3 px-3">
        <div
          v-if="activeComment === comment.name"
          v-for="reply in comment.replies"
          class="flex gap py-2"
          :key="reply.name"
        >
          <Avatar
            :label="reply.owner"
            :image="reply.image"
          />
          <div class="px-2 group">
            <div class="label-group flex gap-1 text-sm items-start">
              <label class="font-medium text-ink-gray-8">{{
                reply.full_name
              }}</label>
              <span class="text-ink-gray-7">{{ " ∙ " }}</span>
              <label class="text-ink-gray-6">{{ comment.created_on }}</label>
            </div>
            <div class="comment-content text-sm mt-1">
              <div v-html="reply.content" />
              <div class="gap-1 mt-2 hidden group-hover:flex">
                <Button
                  variant="subtle"
                  size="xs"
                  class="font-medium"
                >
                  Edit
                </Button>
                <Button
                  variant="subtle"
                  size="xs"
                  class="font-medium"
                  >Delete</Button
                >
              </div>
            </div>
          </div>
        </div>
        <div
          v-else
          class="text-ink-gray-6 font-base text-xs"
        >
          {{ comment.replies.length }}
          {{ comment.replies.length === 1 ? "reply" : "replies" }}
        </div>
        <TextEditor
          v-if="activeComment === comment.name"
          class="border rounded"
          :mentions="allUsers.data"
          editor-class="text-sm p-2"
          placeholder="Reply"
          @change="(val) => (newReplies[comment.name] = val)"
          :bubble-menu="[
            'Bold',
            'Italic',
            'Strikethrough',
            'Separator',
            'Code',
            'Blockquote',
            'Separator',
            ['Bullet List', 'Numbered List'],
          ]"
        >
          <template #bottom>
            <div class="flex justify-end mb-0.5 mr-0.5">
              <Button
                variant="ghost"
                @click="newReply(comment)"
              >
                <template #icon>
                  <LucideCheck class="size-3.5" />
                </template>
              </Button>
            </div>
          </template>
        </TextEditor>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useTemplateRef, computed, reactive, watch } from "vue"
import { allUsers } from "@/resources/permissions"
import { Avatar, Button, TextEditor } from "frappe-ui"
const commentsSection = useTemplateRef("comments-section")

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")
watch(activeComment, (val) => {
  if (val) {
    let el = commentsSection.value.querySelector("#comment-" + val)
    el.scrollIntoView({
      behavior: "smooth",
      block: "start",
      inline: "nearest",
    })
  }
})

const formattedComments = computed(() => {
  return comments.value.map((comment) => {
    let user = allUsers.data.find((k) => k.name == comment.owner)
    comment.full_name = user.full_name
    comment.user_image = user.user_image
    return comment
  })
})

const newReplies = reactive({})

const newReply = (comment) => {
  comment.replies.push({
    content: newReplies[comment.name],
    owner: comment.owner,
    created_on: "Now",
  })
  activeComment.value = ""
}
</script>
<style></style>
