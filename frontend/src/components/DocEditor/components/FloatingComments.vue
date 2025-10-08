<template>
  <div
    v-show="showComments"
    ref="scrollContainer"
    class="relative hidden md:flex min-w-80 border-s-2 flex-col gap-8 justify-start self-stretch pb-5 bg-surface-white"
  >
    <template
      v-for="comment in filteredComments"
      :key="comment.name"
    >
      <div
        :id="'comment-' + comment.name"
        :ref="
          (el) => {
            if (el) commentRefs[comment.name] = el
            else delete commentRefs[comment.name]
          }
        "
        v-on-outside-click="
          (e) => {
            if (
              activeComment === comment.name &&
              !e.target.getAttribute('data-comment-id') &&
              e.target.nodeName === 'DIV' &&
              !comment.new &&
              !e.target.classList?.contains?.('replies-count')
            )
              activeComment = null
          }
        "
        class="absolute rounded shadow w-52 md:w-72 comment-group scroll-m-24 bg-surface-white left-1/2 -translate-x-1/2 opacity-0 transition-[top] duration-100 ease-in-out"
        :class="[
          activeComment === comment.name && 'shadow-xl ',
          comment.top && 'opacity-100',
        ]"
        :style="`top: ${comment.top}px;`"
        @click="activeComment = comment.name"
      >
        <div
          v-show="
            activeComment === comment.name &&
              $store.state.user.id !== 'Guest' &&
              !comment.new &&
              (comment.owner == $store.state.user.id || entity.write)
          "
          class="p-1.5 text-sm flex gap-1 border-b text-ink-gray-9"
          :class="comment.loading && !comment.edit && 'opacity-70'"
        >
          <Button
            v-if="
              !comment.resolved &&
                (comment.owner == $store.state.user.id || entity.write)
            "
            :disabled="comment.loading"
            variant="ghost"
            class="!h-5 !text-xs !px-1.5 !rounded-sm"
            @click="resolve(comment)"
          >
            <template #prefix>
              <LucideCheck class="size-3.5" />
            </template>
            Resolve
          </Button>
          <Button
            v-if="
              comment.resolved &&
                (comment.owner == $store.state.user.id || entity.write)
            "
            :disabled="comment.loading"
            variant="ghost"
            class="!h-5 !text-xs !px-1.5 !rounded-sm"
            @click="resolve(comment, false)"
          >
            <template #prefix>
              <LucideMessageCircleCode class="size-3.5" />
            </template>
            Unresolve
          </Button>
          <Button
            v-if="
              comment.owner == $store.state.user.id ||
                (comment.owner === 'Guest' && entity.write)
            "
            :disabled="comment.loading"
            variant="ghost"
            class="!h-5 !text-xs !px-1.5 !rounded-sm"
            @click="removeComment(comment.name, true)"
          >
            <template #prefix>
              <LucideX class="size-3.5" />
            </template>
            Delete
          </Button>
        </div>
        <div
          class="flex flex-col gap-5 p-3"
          :class="
            activeComment !== comment.name &&
              comment.replies.length > 0 &&
              'pb-1.5'
          "
        >
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
            :class="reply.loading && !reply.edit && 'opacity-70'"
          >
            <div class="w-8 flex justify-center">
              <Avatar
                size="xl"
                class="bg-surface-white"
                :label="$user(reply.owner)?.full_name || reply.owner"
                :image="$user(reply.owner)?.user_image"
              />
            </div>
            <div
              class="grow flex flex-col"
              :class="reply.edit && 'gap-1'"
            >
              <div
                class="w-full flex justify-between items-start label-group gap-1 text-sm"
              >
                <div class="flex gap-1">
                  <label
                    class="font-medium text-ink-gray-8 max-w-[70%] truncate"
                  >{{ $user(reply.owner)?.full_name || reply.owner }}</label>

                  <label class="text-ink-gray-6 truncate">
                    &#183;
                    {{ formatDateOrTime(reply.creation) }}</label>
                </div>
                <Dropdown
                  class="ml-auto opacity-0"
                  :class="
                    activeComment === comment.name &&
                      !reply.edit &&
                      !reply.resolved &&
                      comment.owner == $store.state.user.id &&
                      'opacity-100'
                  "
                  :options="
                    dynamicList([
                      {
                        label: 'Edit',
                        onClick: () => (reply.edit = true),
                        cond: comment.owner == $store.state.user.id,
                      },
                      {
                        label: 'Delete',
                        onClick: () => removeComment(reply.name, false),
                        cond:
                          comment.owner == $store.state.user.id && index !== 0,
                      },
                    ])
                  "
                >
                  <Button
                    :disabled="
                      activeComment !== comment.name ||
                        reply.edit ||
                        reply.resolved
                    "
                    class="!h-5 !text-xs !px-1.5 !rounded-sm opacity-0"
                    :class="
                      activeComment === comment.name &&
                        !reply.edit &&
                        !reply.resolved &&
                        comment.owner == $store.state.user.id &&
                        'opacity-100'
                    "
                    variant="ghost"
                    :icon="h(LucideMoreVertical, { class: 'size-3' })"
                    @click="triggerRoot"
                  />
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
                  @change="setCommentHeights"
                  @submit="
                    () => {
                      reply.content = commentContents[reply.name]
                      reply.edit = false
                      if (reply.new) {
                        createComment.submit({
                          entity_name: props.entity.name,
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
            v-show="
              activeComment === comment.name &&
                !comment.edit &&
                !comment.resolved
            "
            class="flex gap-3"
          >
            <Avatar
              size="xl"
              class="self-center"
              :label="
                $user($store.state.user.id)?.full_name || $store.state.user.id
              "
              :image="$user($store.state.user.id)?.user_image"
            />

            <CommentEditor
              v-model="newReplies[comment.name]"
              placeholder="Reply"
              :is-empty="isEmpty(newReplies[comment.name])"
              @change="setCommentHeights"
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
          class="replies-count text-ink-gray-6 font-base text-xs p-3 pt-0"
        >
          {{ comment.replies.length }}
          {{ comment.replies.length === 1 ? "reply" : "replies" }}
        </div>
      </div>
    </template>
    <div
      class="text-large text-ink-gray-8 font-semibold w-80 px-3 py-2 bg-white dark:bg-black bg-opacity-70 fixed"
    >
      Comments
      <Button
        :icon="LucideX"
        variant="ghost"
        class="float-right"
        @click="showComments = false"
      />
    </div>
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
  h,
  onBeforeUnmount,
  nextTick,
  defineAsyncComponent,
} from "vue"
import { Avatar, Button, createResource, Dropdown } from "frappe-ui"
import { formatDate } from "@/utils/format"
import { dynamicList } from "@/utils/files"
import { v4 } from "uuid"
import { useDebounceFn, useEventListener } from "@vueuse/core"
import { toast } from "@/utils/toasts"
import LucideMessageCircleWarning from "~icons/lucide/message-circle-warning"
import LucideX from "~icons/lucide/x"
import LucideMoreVertical from "~icons/lucide/more-vertical"
import { useStore } from "vuex"

const CommentEditor = defineAsyncComponent(() =>
  import("@/components/DocEditor/components/CommentEditor.vue")
)
const props = defineProps({
  entity: Object,
  editor: Object,
})
const emit = defineEmits(["save"])

const store = useStore()

const activeComment = defineModel("activeComment")
const comments = defineModel("comments")
const showComments = defineModel("showComments")
const scrollContainer = ref("scrollContainer")

const newReplies = reactive({})
const commentRefs = reactive({})
const commentContents = reactive({})

const findComment = (name) => {
  const mainComment = comments.value.find((k) => k.name == name)
  if (mainComment) return mainComment
  for (const c of comments.value) {
    const reply = c.replies.find((k) => k.name == name)
    if (reply) return reply
  }
}

const showResolved = inject("showResolved")
const filteredComments = computed(() => {
  const filtered = showResolved.value
    ? comments.value
    : comments.value.filter((k) => !k.resolved)
  if (!filtered.length) showComments.value = false
  return filtered
})
watch(showResolved, async (val) => {
  await nextTick()
  if (val) {
    document
      .querySelectorAll("[data-resolved=true]")
      .forEach((k) => k.classList.add("display"))
  } else {
    document
      .querySelectorAll("[data-resolved=true]")
      .forEach((k) => k.classList.remove("display"))
  }
})
watch(activeComment, (val) => {
  document
    .querySelector(`span[data-comment-id].active`)
    ?.classList?.remove?.("active")
  setCommentHeights()
  if (val)
    nextTick(() => {
      document
        .querySelector(`span[data-comment-id="${val}"]`)
        .classList.add("active")
    })
})

// Resources
const createComment = createResource({
  url: "drive.api.docs.create_comment",
  onSuccess: () => {
    findComment(createComment.params.name).loading = false
    emit("save")
  },
  onError: () => {
    toast({
      title: "Your comment did not go through. ",
      icon: LucideMessageCircleWarning,
    })
  },
})
const editComment = createResource({
  url: "drive.api.docs.edit_comment",
  onSuccess: () => {
    emit("save")
  },
})
const deleteComment = createResource({
  url: "drive.api.docs.delete_comment",
  onSuccess: () => {
    emit("save")
  },
})
const resolveComment = createResource({
  url: "drive.api.docs.resolve_comment",
  onSuccess: () => {
    emit("save")
  },
})

// Functions
const newReply = (comment, editor) => {
  const name = v4()
  createComment.submit({
    entity_name: props.entity.name,
    parent_name: comment.name,
    name,
    creation: new Date(),
    content: newReplies[comment.name],
    is_reply: true,
  })
  comment.replies.push({
    name,
    content: newReplies[comment.name],
    owner: store.state.user.id,
    creation: new Date(),
    loading: true,
  })
  newReplies[comment.name] = ""
  editor.commands.setContent("")
  setCommentHeights()
}

const removeComment = (name, entire, server = true) => {
  if (server) {
    deleteComment.submit({ name, entire })
  }

  props.editor.commands.unsetComment(name)
  for (const [i, val] of Object.entries(comments.value)) {
    if (val.name === name) {
      comments.value.splice(i, 1)
      break
    }
    for (const [k, reply] of Object.entries(val.replies)) {
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
  props.editor.commands.resolveComment(comment.name, value)
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

const setCommentHeights = useDebounceFn(() => {
  let lastBottom = 0
  nextTick(() => {
    scrollContainer.value.style.height = `max(${scrollContainer.value.parentElement.scrollHeight}px, calc(100vh - 3rem))`
    for (const comment of filteredComments.value) {
      try {
        const containerTop = scrollContainer.value.getBoundingClientRect().top
        const anchorTop =
          document
            .querySelector(`[data-comment-id="${comment.name}"]`)
            .getBoundingClientRect().top - containerTop

        const adjustedTop = Math.max(anchorTop, lastBottom)
        comment.top = adjustedTop
        lastBottom = adjustedTop + commentRefs[comment.name].offsetHeight + 12
      } catch (e) {
        console.log(e)
      }
    }
  })
}, 20)

onMounted(setCommentHeights)
watch(() => filteredComments.value.length, setCommentHeights)
useEventListener(window, "resize", setCommentHeights)
props.editor.on("update", () => {
  const currentNames = new Set()
  setCommentHeights()
  props.editor.state.doc.descendants((node) => {
    node.marks.forEach((mark) => {
      if (mark.type.name === "comment" && mark.attrs.commentId) {
        currentNames.add(mark.attrs.commentId)
      }
    })
  })
  for (const comment of comments.value)
    if (!currentNames.has(comment.name)) removeComment(comment.name, true)
})

const purgeNewEmptyComments = () => {
  for (const comment of comments.value)
    if (comment.new) removeComment(comment.name, true, false)
}
onBeforeUnmount(purgeNewEmptyComments)
useEventListener(window, "beforeunload", purgeNewEmptyComments)
</script>
