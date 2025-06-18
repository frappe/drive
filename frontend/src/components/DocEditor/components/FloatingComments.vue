<template>
  <div
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
      <div class="px-3 py-2.5 text-ink-gray-9">
        <div class="flex gap-2 items-center">
          <Avatar
            :label="comment.owner"
            :image="comment.image"
          />
          <div class="label-group flex flex-col gap-1 text-sm items-start">
            <label class="font-medium text-ink-gray-8">{{
              comment.full_name
            }}</label>

            <label class="text-ink-gray-6">{{
              formatDate(comment.created_on)
            }}</label>
          </div>
        </div>
        <div class="comment-content text-sm my-2">
          <TextEditor
            v-if="comment.edit"
            class="border rounded"
            :content="comment.content"
            :mentions="allUsers.data"
            editor-class="text-sm p-2"
            placeholder="Reply"
            @change="(val) => (commentContents[comment.name] = val)"
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
                  @click="
                    () => {
                      comment.content = commentContents[comment.name]
                      comment.edit = false
                    }
                  "
                >
                  <template #icon>
                    <LucideCheck class="size-3.5" />
                  </template>
                </Button>
              </div>
            </template>
          </TextEditor>
          <template v-else>
            <div v-html="comment.content" />
            <div
              v-show="activeComment === comment.name"
              class="flex gap-1 mt-2"
            >
              <Button
                variant="subtle"
                size="xs"
                class="font-medium"
                @click="comment.edit = true"
              >
                Edit
              </Button>
            </div>
          </template>
        </div>
      </div>
      <div class="pb-3 px-3">
        <div
          v-if="activeComment === comment.name"
          v-for="reply in comment.replies"
          class="py-2"
          :key="reply.name"
        >
          <div class="flex gap-2 items-center">
            <Avatar
              :label="reply.owner"
              :image="reply.image"
            />
            <div class="label-group flex flex-col gap-1 text-sm items-start">
              <label class="font-medium text-ink-gray-8">{{
                reply.full_name
              }}</label>

              <label class="text-ink-gray-6">{{
                formatDate(reply.created_on)
              }}</label>
            </div>
          </div>
          <div class="comment-content text-sm mt-2">
            <TextEditor
              v-if="reply.edit"
              class="border rounded"
              :content="reply.content"
              :mentions="allUsers.data"
              editor-class="text-sm p-2"
              placeholder="Reply"
              @change="(val) => (commentContents[reply.name] = val)"
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
                    @click="
                      () => {
                        reply.content = commentContents[reply.name]
                        reply.edit = false
                      }
                    "
                  >
                    <template #icon>
                      <LucideCheck class="size-3.5" />
                    </template>
                  </Button>
                </div>
              </template>
            </TextEditor>
            <template v-else>
              <div v-html="reply.content" />
              <div class="gap-1 mt-2 hidden group-hover:flex">
                <Button
                  variant="subtle"
                  size="xs"
                  class="font-medium"
                  @click="reply.edit = true"
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
            </template>
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
          v-if="activeComment === comment.name && !comment.edit"
          class="border rounded my-2"
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
import { formatDate } from "@/utils/format"

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")

const formattedComments = computed(() => {
  return comments.value.map((comment) => {
    let user = allUsers.data.find((k) => k.name == comment.owner)
    comment.full_name = user.full_name
    comment.user_image = user.user_image
    return comment
  })
})

const newReplies = reactive({})
const commentContents = reactive({})

const newReply = (comment) => {
  comment.replies.push({
    content: newReplies[comment.name],
    owner: comment.owner,
    created_on: new Date(),
  })
  activeComment.value = ""
}
</script>
<style></style>
