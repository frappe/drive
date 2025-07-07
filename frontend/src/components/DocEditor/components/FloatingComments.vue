<template>
  <Teleport
    to="#navbar-content"
    v-if="filteredComments.length > 0"
  >
    <Switch
      size="sm"
      label="Comments"
      description=""
      v-model="showComments"
    />
  </Teleport>
  <div
    ref="scrollContainer"
    v-show="showComments"
    class="relative border-s-2 w-80 flex flex-col gap-8 justify-start self-stretch pb-5"
  >
    <div
      class="text-large text-ink-gray-8 font-semibold w-80 px-3 py-2 bg-surface-white z-[100] fixed"
    >
      Comments
    </div>
    <template
      v-for="comment in filteredComments"
      :key="comment.name"
    >
      <div
        v-on-outside-click="(e) => {}"
        ref="commentRefs"
        :id="'comment-' + comment.name"
        @click="activeComment = comment.name"
        class="absolute rounded shadow w-52 md:w-72 comment-group scroll-m-8 bg-surface-white left-1/2 -translate-x-1/2 opacity-0 transition-[top] duration-100 ease-in-out"
        :class="[
          activeComment === comment.name && 'shadow-xl ',
          comment.top && 'opacity-100',
        ]"
        :style="`top: ${comment.top}px;`"
      >
        <div
          v-show="activeComment === comment.name && !comment.new"
          class="p-1.5 text-sm flex gap-1 border-b text-ink-gray-9"
        >
          <Button
            v-if="!comment.resolved"
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
            v-if="comment.resolved"
            variant="ghost"
            size="xs"
            @click="resolve(comment, false)"
          >
            <template #prefix>
              <LucideMessageCircleCode class="size-3.5" />
            </template>
            Unresolve
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
        <div class="flex flex-col p-3 gap-5">
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
            class="group w-full flex gap-3"
          >
            <div class="w-8 flex justify-center">
              <Avatar
                size="xl"
                class="bg-surface-white"
                :label="reply.owner"
                :image="$user(reply.owner).user_image"
              />
            </div>
            <div
              class="grow flex flex-col"
              :class="reply.edit && 'gap-1'"
            >
              <div
                class="w-full flex justify-between items-start label-group gap-1 text-sm"
              >
                <label class="font-medium text-ink-gray-8">{{
                  $user(reply.owner).full_name
                }}</label>

                <label class="text-ink-gray-6 truncate">
                  &#183;
                  {{ formatDateOrTime(reply.creation) }}</label
                >
                <Dropdown
                  class="ml-auto opacity-0 disabled"
                  :class="
                    activeComment === comment.name &&
                    !reply.edit &&
                    !reply.resolved &&
                    'opacity-100'
                  "
                  :options="
                    index === 0
                      ? [
                          {
                            onClick: () => (reply.edit = true),
                            label: 'Edit',
                          },
                        ]
                      : [
                          {
                            onClick: () => (reply.edit = true),
                            label: 'Edit',
                          },
                          {
                            label: 'Delete',
                            onClick: () => removeComment(reply.name, false),
                          },
                        ]
                  "
                >
                  <Button
                    :disabled="
                      activeComment !== comment.name ||
                      reply.edit ||
                      reply.resolved
                    "
                    size="xs"
                    variant="ghost"
                    @click="triggerRoot"
                  >
                    <LucideMoreVertical class="size-3" />
                  </Button>
                </Dropdown>
                <LucideBadgeCheck
                  v-if="comment.resolved"
                  class="text-ink-gray-6 size-4"
                />
              </div>
              <div class="comment-content text-sm">
                <CommentEditor
                  v-model="commentContents[reply.name]"
                  placeholder="Edit"
                  :disabled="
                    isEmpty(commentContents[reply.name]) ||
                    commentContents[reply.name] == reply.content
                  "
                  :editable="reply.edit === true"
                  :content="reply.content"
                  @submit="
                    () => {
                      reply.content = commentContents[reply.name]
                      reply.edit = false
                      if (reply.new) {
                        createComment.submit({
                          parent: entityName,
                          content: reply.content,
                          name: reply.name,
                          is_reply: false,
                        })
                        delete reply.new
                      } else {
                        editComment.submit(reply)
                      }
                    }
                  "
                  @cancel="
                    (editor) => {
                      if (reply.new) {
                        removeComment(reply.name, false, false)
                      } else {
                        editor.commands.setContent(reply.content)
                        reply.edit = false
                      }
                    }
                  "
                />
              </div>
            </div>
          </div>

          <div
            class="flex gap-3"
            v-show="
              activeComment === comment.name &&
              !comment.edit &&
              !comment.resolved
            "
          >
            <Avatar
              size="xl"
              class="self-center"
              :label="$user($store.state.user.id).full_name"
              :image="$user($store.state.user.id).user_image"
            />

            <CommentEditor
              v-model="newReplies[comment.name]"
              placeholder="Reply"
              :is-empty="isEmpty(newReplies[comment.name])"
              @submit="(editor) => newReply(comment, editor)"
              @cancel="
                (editor) => {
                  newReplies[comment.name] = ''
                  editor.commands.setContent('')
                  editor.commands.blur()
                }
              "
            />
          </div>
        </div>
        <div
          v-if="activeComment !== comment.name && comment.replies.length > 0"
          class="text-ink-gray-6 font-base text-xs p-2.5 pt-0"
        >
          {{ comment.replies.length }}
          {{ comment.replies.length === 1 ? "reply" : "replies" }}
        </div>
      </div>
    </template>
  </div>
</template>
<script setup>
import {
  computed,
  reactive,
  watch,
  inject,
  onMounted,
  ref,
  onBeforeUnmount,
} from "vue"
import { Avatar, Button, createResource, Dropdown, Switch } from "frappe-ui"
import { formatDate } from "@/utils/format"
import { v4 } from "uuid"
import CommentEditor from "./CommentEditor.vue"
import { useDebounceFn, useEventListener } from "@vueuse/core"

const props = defineProps({
  entityName: String,
  editor: Object,
})

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")
const commentRefs = ref([])
const scrollContainer = ref("scrollContainer")

const newReplies = reactive({})
const commentContents = reactive({})

const showResolved = inject("showResolved")
const filteredComments = computed(() =>
  showResolved.value
    ? props.comments
    : props.comments.filter((k) => !k.resolved)
)
const showComments = ref(filteredComments.value.length > 0)

watch(activeComment, (val) => {
  const currentEl = document.querySelector(".active")
  if (currentEl) currentEl.classList?.remove?.("active")
  setCommentHeights()
  if (!val) return
  // Sometimes remove runs after adding the class :woozy:
  document
    .querySelector(`span[data-comment-id="${val}"]`)
    .classList.add("active")
})

// Resources
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

// Functions
const newReply = (comment, editor) => {
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
  newReplies[comment.name] = ""
  editor.commands.setContent("")
}

const removeComment = (name, entire, server = true) => {
  if (server) deleteComment.submit({ name, entire })
  props.editor.commands.unsetComment(name)
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
  setCommentHeights()
}

const resolve = (comment, value = true) => {
  resolveComment.submit({ name: comment.name, value })
  props.editor.commands.resolveComment(comment.name)
  comment.resolved = value
}

const isEmpty = (editorContent) => {
  return (
    !editorContent ||
    !editorContent.length ||
    editorContent.replace(/\s/g, "") == "<p></p>"
  )
}

const formatDateOrTime = (datetimeStr) => {
  const now = new Date()
  const datetime = new Date(datetimeStr)
  const isToday =
    datetime.getDate() === now.getDate() &&
    datetime.getMonth() === now.getMonth() &&
    datetime.getFullYear() === now.getFullYear()
  const [dateStr, timeStr] = formatDate(datetime).split(", ")
  return isToday ? timeStr : dateStr
}

const setCommentHeights = () => {
  let lastBottom = 0
  setTimeout(() => {
    scrollContainer.value.style.height = `max(${scrollContainer.value.parentElement.scrollHeight}px, calc(100vh - 3rem))`
    for (let [index, comment] of Object.entries(filteredComments.value)) {
      try {
        const containerTop = scrollContainer.value.getBoundingClientRect().top
        const anchorTop =
          document
            .querySelector(`[data-comment-id="${comment.name}"]`)
            .getBoundingClientRect().top - containerTop

        const adjustedTop = Math.max(anchorTop, lastBottom)
        comment.top = adjustedTop

        lastBottom = adjustedTop + commentRefs.value[index].offsetHeight + 12
      } catch {}
    }
  }, 100)
}

onMounted(setCommentHeights)
const debouncedSetCommentHeights = useDebounceFn(setCommentHeights, 20)
useEventListener(window, "resize", debouncedSetCommentHeights)

props.editor.on("update", () => {
  const currentNames = new Set()
  debouncedSetCommentHeights()
  props.editor.state.doc.descendants((node) => {
    node.marks.forEach((mark) => {
      if (mark.type.name === "comment" && mark.attrs.commentId) {
        currentNames.add(mark.attrs.commentId)
      }
    })
  })
  for (let comment of comments.value)
    if (!currentNames.has(comment.name)) removeComment(comment.name, true)
  setCommentHeights()
})

const purgeNewEmptyComments = () => {
  for (const comment of comments.value)
    if (comment.new) removeComment(comment.name, true, false)
}
onBeforeUnmount(purgeNewEmptyComments)
useEventListener(window, "beforeunload", purgeNewEmptyComments)
</script>
