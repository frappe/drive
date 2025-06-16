<template>
  <div class="select-text">
    <div class="flex items-center justify-start mb-6">
      <span
        class="inline-flex items-center gap-2.5 text-ink-gray-8 font-medium text-lg w-full"
      >
        Annotations
      </span>
      <Dropdown
        :options="filterItems"
        placement="left"
      >
        <Button>
          <template #prefix>
            <LucideFilter class="size-4 text-ink-gray-6" />
          </template>
          {{ currentFilterLabel }}
        </Button>
      </Dropdown>
    </div>
    <div class="divide-y space-y-4">
      <!-- root annotations -->
      <div
        v-if="currentFilter.length"
        class="current-comment my-4"
        @click="
          emit('setActiveAnnotation', comment),
            (currentActiveAnnotation = comment)
        "
        :class="
          comment.get('id') === activeAnnotation ? 'active' : 'cursor-pointer'
        "
        v-for="(comment, i) in currentFilter"
      >
        <div class="mt-4 flex py-0.5 mb-2 gap-x-2 text-sm items-center">
          <Avatar
            size="md"
            :label="comment.get('owner')"
            :image="comment.get('ownerImage')"
            class="mr-1"
          />
          <div class="flex flex-col gap-y-0.5 mb-1">
            <div class="flex items-center gap-x-0.5">
              <span class="text-ink-gray-8 text-sm font-medium">
                {{ comment.get("owner") }}
              </span>
              <span class="text-ink-gray-7 text-sm">{{ " ∙ " }}</span>
              <span class="text-ink-gray-7 text-sm">
                {{ useTimeAgo(comment.get("createdAt")) }}
              </span>
            </div>
            <span class="text-sm text-ink-gray-7">
              {{ comment.get("replies").length }}
              {{ comment.get("replies").length === 1 ? " reply" : "replies" }}
            </span>
          </div>

          <Dropdown
            v-if="
              comment.get('id') === activeAnnotation &&
              (entity.write === 1 ||
                comment.get('ownerEmail') === currentUserEmail)
            "
            :options="commentOptions"
            placement="right"
            class="ml-auto mb-auto"
          >
            <Button
              size="sm"
              variant="ghost"
              icon="more-horizontal"
            />
          </Dropdown>
        </div>
        <div class="pl-10 text-sm leading-5">
          <span
            id="injected"
            v-html="comment.get('content')"
            class="max-w-full break-word text-sm text-ink-gray-7"
          >
          </span>
        </div>

        <!-- replies for current annotation -->
        <div v-if="comment.get('id') === activeAnnotation">
          <div
            class="mt-6"
            v-for="(reply, j) in comment.get('replies')"
          >
            <div
              class="flex py-0.5 gap-x-0.5 text-sm justify-start items-center mb-1.5"
            >
              <Avatar
                size="md"
                :label="reply.get('owner')"
                :image="reply.get('ownerImage')"
                class="mr-2"
              />
              <span class="text-ink-gray-8 text-sm font-medium">
                {{ reply.get("owner") }}
              </span>
              <span class="text-ink-gray-7 text-sm">{{ " ∙ " }}</span>
              <span class="text-ink-gray-7 text-sm">
                {{ useTimeAgo(reply.get("createdAt")) }}
              </span>
              <Dropdown
                v-if="
                  entity.owner === 'You' ||
                  reply.get('ownerEmail') === currentUserEmail
                "
                :options="replyOptions"
                placement="right"
                class="ml-auto"
              >
                <Button
                  size="sm"
                  variant="ghost"
                  icon="more-horizontal"
                  @click="currentActiveReplyAnnotation = reply"
                />
              </Dropdown>
            </div>
            <div class="pl-9 -mt-1.5 text-sm leading-5">
              <span
                id="injected"
                v-html="reply.get('content')"
                class="max-w-full break-word text-ink-gray-7"
              >
              </span>
            </div>
          </div>

          <section
            v-if="comment.get('id') === activeAnnotation"
            class="flex flex-col gap-2"
          >
            <div class="flex items-center justify-start gap-2 mt-6 mb-2">
              <Avatar
                size="md"
                :label="fullName"
                :image="imageURL"
                class=""
              />

              <TiptapInput
                v-model="commentText"
                @success="addReply(comment.get('id'))"
                @keyup.ctrl.enter="addReply(comment.get('id'))"
              />
            </div>
          </section>
        </div>
      </div>

      <div
        v-else
        class="text-ink-gray-5 text-sm my-5"
      >
        There are annotations for the current document or category
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useStore } from "vuex"
import { ref, computed, inject } from "vue"
import { Avatar, Button, Dropdown } from "frappe-ui"
import { v4 as uuidv4 } from "uuid"
import { useTimeAgo } from "@vueuse/core"
import * as Y from "yjs"
import TiptapInput from "@/components/TiptapInput.vue"

const store = useStore()

const emit = defineEmits([
  "setActiveAnnotation",
  /* "update:allAnnotations", */
  "update:activeAnnotation",
])

interface Props {
  activeAnnotation: string
  showAnnotations: boolean
}
const doc = inject("document")
const editor = inject("editor")
const props = defineProps<Props>()
const allAnnotations = doc.value.getArray("docAnnotations")

const currentActiveAnnotation = ref()
const currentActiveReplyAnnotation = ref()
const currentFilterLabel = ref("Open")
const currentFilterState = ref(0)
const commentText = ref<string>("")

const fullName = computed(() => store.state.user.fullName)
const email = computed(() => store.state.user.id)
const imageURL = computed(() => store.state.user.imageURL)
const currentUserEmail = computed(() => store.state.user.id)
const entity = computed(() => store.state.activeEntity)

const openAndAnchoredAnnotations = computed(() => {
  let arr = allAnnotations.toArray()
  return arr.filter(
    (item) => item.get("anchor") === 1 && item.get("resolved") === 0
  )
})

const openAnnotations = computed(() => {
  let arr = allAnnotations.toArray()
  return arr.filter(
    (item) => item.get("anchor") === 0 && item.get("resolved") === 0
  )
})

const allResolvedAnnotations = computed(() => {
  let arr = allAnnotations.toArray()
  return arr.filter((item) => item.get("resolved") === 1)
})

const currentFilter = computed(() => {
  switch (currentFilterState.value) {
    case 0:
      currentFilterLabel.value = "Open"
      return openAndAnchoredAnnotations.value
    case 1:
      currentFilterLabel.value = "Unanchored"
      return openAnnotations.value
    case 2:
      currentFilterLabel.value = "Resolved"
      return allResolvedAnnotations.value
    default:
      return openAndAnchoredAnnotations.value
  }
})

const filterItems = computed(() => {
  return [
    {
      label: "Open",
      onClick: () => {
        currentFilterState.value = 0
      },
    },
    {
      label: "Unanchored",
      onClick: () => {
        currentFilterState.value = 1
      },
    },
    {
      label: "Resolved",
      onClick: () => {
        currentFilterState.value = 2
      },
    },
  ].filter((item, index) => index !== currentFilterState.value)
})

const addReply = (parentID) => {
  const newID = uuidv4()
  const newReplyYmap = new Y.Map()
  let parent
  for (const value of allAnnotations) {
    if (value.get("id") === parentID) {
      parent = value
      break
    }
  }
  commentText.value = commentText.value.replace(/<p>(\s|&nbsp;)*<\/p>$/, "") // trim trailing p tags
  let replies_arr = parent.get("replies")
  newReplyYmap.set("id", newID)
  newReplyYmap.set("content", commentText.value)
  newReplyYmap.set("owner", fullName.value)
  newReplyYmap.set("owner", fullName.value)
  newReplyYmap.set("ownerEmail", email.value)
  newReplyYmap.set("ownerImage", imageURL.value)
  newReplyYmap.set("createdAt", Date.now())
  replies_arr.push([newReplyYmap])
  /*     let newReply = {
      id: uuidv4(),
      enabled: 1,
      parentID: parentID,
      content: commentText.value,
      owner: fullName.value,
      ownerEmail: email.value,
      createdAt: Date.now(),
    };
    let pval
    for (const value of allAnnotations) {
      if (value.id === parentID){
        pval = value
        break
      }

     }
 */
  /*     console.log(pval)
    pval.replies.push(newReply) */
  /* let parentComment = props.allAnnotations.find((item) => item.id === parentID);
    if (parentComment && Array.isArray(parentComment.replies)) {
      parentComment.replies.push(newReply);
    } */
  commentText.value = ""
}

const commentOptions = computed(() =>
  [
    {
      label: "Mark as Resolved",
      onClick: () => {
        allAnnotations.forEach((yMap) => {
          if (yMap.get("id") === currentActiveAnnotation.value.get("id")) {
            yMap.set("resolved", 1)
            editor.value
              .chain()
              .unsetAnnotation(currentActiveAnnotation.value.get("id"))
              .run()
          }
        })
      },
      isEnabled: () => {
        return (
          !currentActiveAnnotation?.value?.get("resolved") &&
          (currentActiveAnnotation?.value?.get("ownerEmail") ===
            currentUserEmail ||
            entity.value.write)
        )
      },
    },
    {
      label: "Mark as Open",
      onClick: () => {
        allAnnotations.forEach((yMap) => {
          if (yMap.get("id") === currentActiveAnnotation.value.get("id")) {
            yMap.set("resolved", 0)
            editor.value
              .chain()
              .setAnnotation(currentActiveAnnotation.value.get("id"))
              .run()
          }
        })
      },
      isEnabled: () => {
        return (
          currentActiveAnnotation?.value?.get("resolved") &&
          (currentActiveAnnotation?.value?.get("ownerEmail") ===
            currentUserEmail ||
            entity.value.write)
        )
      },
    },

    {
      label: "Delete",
      onClick: () => {
        editor.value
          .chain()
          .unsetAnnotation(currentActiveAnnotation.value.get("id"))
          .run()
        wipeEntryById(allAnnotations, currentActiveAnnotation.value.get("id"))
      },
      isEnabled: () => {
        return true
      },
    },
  ].filter((item) => item.isEnabled())
)

const replyOptions = computed(() =>
  [
    /* {
      label: "Edit",
      onClick: () => {},
      isEnabled: () => {
        return (
          currentActiveReplyAnnotation?.value?.get("ownerEmail") ===
          currentUserEmail.value
        )
      },
    }, */
    {
      label: "Delete",
      onClick: () => {
        let yarray = allAnnotations
        let targetId = currentActiveAnnotation.value.get("id")

        parentLoop: for (let i = 0; i < yarray.length; i++) {
          const ymap = yarray.get(i)

          if (ymap.get("id") === targetId) {
            let replies = ymap.get("replies")

            for (let j = 0; j < replies.length; j++) {
              const replyMap = replies.get(j)
              if (
                replyMap.get("id") ===
                currentActiveReplyAnnotation.value.get("id")
              ) {
                replies.delete(j)
                break parentLoop
                return
              }
            }
          }
        }
      },
      isEnabled: () => {
        return (
          currentActiveReplyAnnotation?.value?.get("ownerEmail") ===
            currentUserEmail.value || entity.value.owner === "You"
        )
      },
    },
  ].filter((item) => item.isEnabled())
)

// Move 'resolve' operations to a similar for loop
// exit early instead of forEach
function wipeEntryById(yarray, targetId) {
  for (let index = 0; index < yarray.length; index++) {
    const ymap = yarray.get(index)
    if (ymap.get("id") === targetId) {
      yarray.delete(index)
      break
      return
    }
  }
}
</script>

<style>
.current-comment {
  /* transition: all 0.1s cubic-bezier(0.165, 0.84, 0.44, 1); */
  transition: all 0.1s ease-in-out;
}

#injected p:empty::after {
  content: "\A"; /* Inserts a line break */
  white-space: pre; /* Preserves white space */
}

.current-comment.active {
  padding: 15px 0px;
}

.slide-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>
