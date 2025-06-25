<template>
  <div
    v-show="filteredComments.length > 0"
    class="border-s-2 px-12 pt-6 pb-[100%] flex flex-col gap-8 justify-start max-h-full overflow-auto"
  >
    <div
      v-for="comment in filteredComments"
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
          @click="resolve(comment)"
        >
          <template #prefix>
            <LucideCheck class="size-3.5" />
          </template>
          Resolve
        </Button>
        <Button
          variant="ghost"
          size="xs"
          @click="removeComment(comment.name, true)"
        >
          <template #prefix>
            <LucideX class="size-3.5" />
          </template>
          Delete
        </Button>
      </div>
      <div class="flex flex-col p-2.5 gap-2.5">
        <div
          v-for="(reply, index) in activeComment === comment.name
            ? [
                comment,
                ...comment.replies.toSorted((a, b) =>
                  new Date(a.creation) > new Date(b.creation) ? 1 : -1
                ),
              ]
            : [comment]"
          :key="reply.name"
          class="group flex flex-col gap-2.5"
        >
          <div class="flex justify-between">
            <div class="flex gap-2.5 items-center">
              <Avatar
                :label="reply.owner"
                :image="$user(reply.owner).user_image"
              />
              <div class="label-group flex flex-col gap-1 text-sm items-start">
                <label class="font-medium text-ink-gray-8">{{
                  $user(reply.owner).full_name
                }}</label>

                <label class="text-ink-gray-6">{{
                  formatDate(reply.creation)
                }}</label>
              </div>
            </div>
            <Dropdown
              v-if="activeComment === comment.name && !reply.edit"
              :options="
                index === 0
                  ? [{ onClick: () => (reply.edit = true), label: 'Edit' }]
                  : [
                      { onClick: () => (reply.edit = true), label: 'Edit' },
                      {
                        label: 'Delete',
                        onClick: () => removeComment(reply.name, false),
                      },
                    ]
              "
            >
              <Button
                size="xs"
                variant="ghost"
                @click="triggerRoot"
              >
                <LucideMoreVertical class="size-3" />
              </Button>
            </Dropdown>
          </div>
          <div class="comment-content text-sm">
            <TextEditor
              :editable="reply.edit === true"
              :content="reply.content"
              :mentions="allUsers.data"
              :editor-class="[
                'text-p-sm',
                reply.edit && 'p-1.5 border rounded',
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
                <div
                  v-if="reply.edit"
                  class="flex gap-2 mt-2"
                >
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
                        if (reply.new) {
                          removeComment(reply.name, false, false)
                        } else {
                          editor.commands.setContent(reply.content)
                          reply.edit = false
                        }
                      }
                    "
                    >Cancel</Button
                  >
                </div></template
              >
            </TextEditor>
          </div>
        </div>
        <div
          v-if="activeComment !== comment.name"
          class="text-ink-gray-6 font-base text-xs"
        >
          {{ comment.replies.length }}
          {{ comment.replies.length === 1 ? "reply" : "replies" }}
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
import { Avatar, Button, TextEditor, createResource, Dropdown } from "frappe-ui"
import { formatDate } from "@/utils/format"
import { v4 } from "uuid"
import { comment } from "postcss"
import { LucideMoreVertical } from "lucide-vue-next"

const props = defineProps({
  doc: String,
  editor: Object,
})

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")

const filteredComments = computed(() =>
  props.comments.filter((k) => !k.resolved)
)

const createComment = createResource({
  url: "drive.api.files.create_comment",
})
const editComment = createResource({
  url: "drive.api.files.edit_comment",
})
const deleteComment = createResource({
  url: "drive.api.files.delete_comment",
})
const resolveComment = createResource({
  url: "drive.api.files.resolve_comment",
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

const removeComment = (name, entire, server = true) => {
  if (server) deleteComment.submit({ name, entire })
  for (let [i, val] of Object.entries(comments.value)) {
    if (val.name === name) {
      comments.value.splice(i, 1)
      break
    }
    for (let [k, reply] of Object.entries(val.replies)) {
      if (reply.name === name) {
        val.replies.splice(k, 1)
        break
      }
    }
  }
}

const resolve = (comment) => {
  resolveComment.submit({ name: comment.name })
  props.editor.commands.resolveComment(comment.name)
  comment.resolved = true
}

watch(activeComment, (val) => {
  if (!val) return
  document.querySelector(".active")?.classList?.remove?.("active")
  // Sometimes remove runs after adding the class :woozy:
  setTimeout(
    () =>
      document
        .querySelector(`span[data-comment-id="${val}"]`)
        .classList.add("active"),
    100
  )
})
</script>
