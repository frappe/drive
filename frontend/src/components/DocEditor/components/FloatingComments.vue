<template>
  <div
    class="border-s-2 px-12 pt-6 pb-[100%] flex flex-col gap-8 justify-start max-h-full overflow-auto"
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
          @click="deleteComment.submit({ name: comment.name, entire: true })"
        >
          <template #prefix>
            <LucideX class="size-3.5" />
          </template>
          Delete
        </Button>
      </div>
      <div class="flex flex-col p-3 gap-4">
        <div
          v-for="(reply, index) in [comment, ...comment.replies]"
          class="group"
          :key="reply.name"
        >
          <template v-if="index === 0 || activeComment === comment.name">
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
                  formatDate(reply.creation)
                }}</label>
              </div>
            </div>
            <div class="comment-content text-sm mt-1">
              <TextEditor
                :editable="reply.edit === true"
                :content="reply.content"
                :mentions="allUsers.data"
                :editor-class="[
                  'text-p-sm',
                  reply.edit && 'p-2 border rounded',
                ]"
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
                <template #bottom="{ editor }">
                  <div class="flex gap-2 mt-2">
                    <template
                      v-if="!reply.edit"
                      v-show="index"
                    >
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
                        @click="removeComment(reply.name)"
                        >Delete</Button
                      >
                    </template>
                    <template v-else>
                      <Button
                        variant="solid"
                        size="xs"
                        class="font-medium"
                        @click="
                          () => {
                            reply.content = commentContents[reply.name]
                            reply.edit = false
                            if (reply.new) {
                              createComment.submit({
                                parent: doc,
                                content: reply.content,
                                name: reply.name,
                                is_reply: false,
                              })
                            } else {
                              editComment.submit(reply)
                            }
                          }
                        "
                      >
                        Submit
                      </Button>
                      <Button
                        size="xs"
                        class="font-medium"
                        @click="
                          () => {
                            editor.commands.setContent(reply.content)
                            reply.edit = false
                          }
                        "
                        >Cancel</Button
                      >
                    </template>
                  </div></template
                >
              </TextEditor>
            </div>
          </template>
          <div
            v-else
            class="text-ink-gray-6 font-base text-xs"
          >
            {{ comment.replies.length }}
            {{ comment.replies.length === 1 ? "reply" : "replies" }}
          </div>
        </div>
        <div v-if="activeComment === comment.name && !comment.edit">
          <TextEditor
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
          />
          <Button
            v-if="newReplies[comment.name]?.length"
            variant="solid"
            size="xs"
            class="font-medium mt-2"
            @click="newReply(comment)"
          >
            Submit
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useTemplateRef, computed, reactive, watch, onMounted } from "vue"
import { allUsers } from "@/resources/permissions"
import { Avatar, Button, TextEditor, createResource } from "frappe-ui"
import { formatDate } from "@/utils/format"
import { v4 } from "uuid"

const props = defineProps({
  doc: String,
  editor: Object,
})

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")

const createComment = createResource({
  url: "drive.api.files.create_comment",
})
const editComment = createResource({
  url: "drive.api.files.edit_comment",
})
const deleteComment = createResource({
  url: "drive.api.files.delete_comment",
})

const formattedComments = computed(() => {
  comments.value.forEach((comment) => {
    let user = allUsers.data.find((k) => k.name == comment.owner)
    comment.full_name = user.full_name
    comment.user_image = user.user_image
  })
  return comments.value
})

const newReplies = reactive({})
const commentContents = reactive({})

const newReply = (comment) => {
  const name = v4()
  createComment.submit({
    parent: comment.name,
    name,
    creation: new Date(),
    content: newReplies[comment.name],
    is_reply: true,
  })
  comment.replies.push({
    name,
    content: newReplies[comment.name],
    owner: comment.owner,
    creation: new Date(),
  })
  activeComment.value = ""
}

const removeComment = (name) => {
  props.editor.commands.unsetComment(name)
  deleteComment.submit({ name })
  for (let [i, val] of Object.entries(comments.value)) {
    if (val.name === name) {
      console.log(val, name)
      comments.value.pop(i)
      break
    }
    for (let [k, reply] of Object.entries(val.replies)) {
      if (reply.name === name) {
        console.log(reply, name)
        val.replies.pop(k)
        break
      }
    }
  }
}

watch(activeComment, (val) => {
  if (!val) return
  document.querySelector(".active")?.classList?.remove?.("active")
  try {
    const el = document.querySelector(`span[data-comment-id=${val}]`)
    if (el) el.classList.add("active")
  } catch {}
})
</script>
