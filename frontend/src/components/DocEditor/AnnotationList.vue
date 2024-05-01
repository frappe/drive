<template>
  <div>
    <div class="flex items-center justify-start mb-6">
      <span class="font-medium text-base">Annotations</span>
      <Button
        @click="showCommentHistory = true"
        variant="ghost"
        size="sm"
        class="ml-auto"
        ><History class="w-4 h-auto text-gray-700 stroke-[1.5]"
      /></Button>
    </div>
    <div class="divide-y space-y-2">
      <div
        class="current-comment"
        @click="emit('setActiveComment', comment)"
        :class="
          comment.get('id') === activeCommentID ? 'active' : 'cursor-pointer'
        "
        v-for="(comment, i) in enabledComments"
      >
        <div class="mt-4 flex py-0.5 mb-2 gap-x-2 text-sm items-center">
          <Avatar
            size="lg"
            :label="comment.get('owner')"
            :imageURL="comment.get('email')"
            class="mr-1"
          />
          <div class="flex flex-col">
            <div class="flex items-center gap-x-0.5">
              <span class="text-gray-800 text-sm font-medium">
                {{ comment.get("owner") }}
              </span>
              <span class="text-gray-700 text-sm">{{ " ∙ " }}</span>
              <span class="text-gray-700 text-sm">
                {{ formatDate(comment.get("createdAt")) }}
              </span>
            </div>
            <span class="text-xs text-gray-600">
              {{ comment.get("replies").length }}
              {{ comment.get("replies").length === 1 ? " reply" : "replies" }}
            </span>
          </div>

          <Dropdown :options="commentOptions" placement="right" class="ml-auto">
            <Button size="sm" variant="ghost" icon="more-horizontal" />
          </Dropdown>
        </div>
        <div class="pl-10 text-sm leading-5">
          <span class="max-w-full break-word text-sm text-gray-700">
            {{ comment.get("content") }}
          </span>
        </div>
        <div v-if="comment.get('id') === activeCommentID">
          <div class="my-4" v-for="(reply, j) in comment.get('replies')">
            <div
              class="flex py-0.5 mb-0.5 gap-x-0.5 text-sm justify-start items-center"
            >
              <Avatar
                size="lg"
                :label="reply.get('owner')"
                :imageURL="reply.get('email')"
                class="mr-2"
              />
              <span class="text-gray-800 text-sm font-medium">
                {{ reply.get("owner") }}
              </span>
              <span class="text-gray-700 text-sm">{{ " ∙ " }}</span>
              <span class="text-gray-700 text-sm">
                {{ formatDate(reply.get("createdAt")) }}
              </span>
              <Dropdown
                :options="commentOptions"
                placement="right"
                class="ml-auto"
              >
                <Button size="sm" variant="ghost" icon="more-horizontal" />
              </Dropdown>
            </div>
            <div class="pl-10 -mt-1.5 text-sm leading-5">
              <span class="max-w-full break-word text-gray-700">
                {{ reply.get("content") }}
              </span>
            </div>
          </div>

          <section
            v-if="comment.get('id') === activeCommentID"
            class="flex flex-col gap-2 mt-3 py-3"
          >
            <div class="flex items-center justify-start gap-2">
              <Avatar size="lg" :label="fullName" :image="imageURL" class="" />
              <div
                class="flex items-center w-full border rounded pr-2 hover:bg-gray-100"
              >
                <textarea
                  :ref="
                    (el) => {
                      textarea[comment.get('id')] = el
                    }
                  "
                  class="w-full h-7 placeholder-gray-500 max-h-[60vh] overflow-y-hidden form-textarea block bg-transparent border-0 shadow- mx-0.5 resize-none focus:outline-0 focus:border-0 active:outline-0 hover:bg-transparent"
                  v-model="commentText"
                  placeholder="Reply"
                  @input="resize($event)"
                  @keypress.enter.stop.prevent="addReply(comment.get('id'))"
                ></textarea>
                <Button
                  class="w-auto"
                  :variant="'ghost'"
                  icon="arrow-up-circle"
                  :disabled="!commentText.length"
                  @click="addReply(comment.get('id'))"
                ></Button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
    <Dialog
      v-if="showCommentHistory"
      v-model="showCommentHistory"
      :options="{
        title: 'Comment History',
        size: 'md',
      }"
    >
      <template #body>
        <div
          class="flex flex-col px-4 pb-6 pt-5 sm:px-6"
          :style="{ height: 'auto', maxHeight: 'calc(70vh)' }"
        >
          <h1 class="text-xl font-semibold leading-6 text-gray-900">
            Annotation History
          </h1>
          <span class="text-sm py-1 mb-4 text-gray-600">
            Annotations without an anchor or those that are resolved
          </span>
          <div class="divide-y space-y-5 overflow-y-scroll">
            <div
              class="current-comment"
              @click="emit('setActiveComment', comment)"
              :class="
                comment.get('id') === activeCommentID
                  ? 'active'
                  : 'cursor-pointer'
              "
              v-for="(comment, i) in disabledComments"
            >
              <!--   -->
              <div class="mt-4 flex py-0.5 mb-2 gap-x-2 text-sm items-center">
                <Avatar
                  size="lg"
                  :label="comment.get('owner')"
                  :imageURL="comment.get('email')"
                  class="mr-1"
                />
                <div class="flex flex-col">
                  <div class="flex items-center gap-x-0.5">
                    <span class="text-gray-800 text-sm font-medium">
                      {{ comment.get("owner") }}
                    </span>
                    <span class="text-gray-700 text-sm">{{ " ∙ " }}</span>
                    <span class="text-gray-700 text-sm">
                      {{ formatDate(comment.get("createdAt")) }}
                    </span>
                  </div>
                  <span class="text-xs text-gray-600">
                    {{ comment.get("replies").length }}
                    {{
                      comment.get("replies").length === 1 ? " reply" : "replies"
                    }}
                  </span>
                </div>
                <div
                  :class="
                    comment.get('anchor') == 1 ? 'bg-green-400' : 'bg-red-400'
                  "
                >
                  <Dropdown
                    :options="commentOptions"
                    placement="right"
                    class="ml-auto"
                  >
                    <Button size="sm" variant="ghost" icon="more-horizontal" />
                  </Dropdown>
                </div>
              </div>
              <div class="pl-10 text-sm leading-5">
                <span class="max-w-full break-word text-sm text-gray-700">
                  {{ comment.get("content") }}
                </span>
              </div>
              <div v-if="comment.get('id') === activeCommentID">
                <div class="my-4" v-for="(reply, j) in comment.get('replies')">
                  <div
                    class="flex py-0.5 mb-0.5 gap-x-0.5 text-sm justify-start items-center"
                  >
                    <Avatar
                      size="lg"
                      :label="reply.get('owner')"
                      :imageURL="reply.get('email')"
                      class="mr-2"
                    />
                    <span class="text-gray-800 text-sm font-medium">
                      {{ reply.get("owner") }}
                    </span>
                    <span class="text-gray-700 text-sm">{{ " ∙ " }}</span>
                    <span class="text-gray-700 text-sm">
                      {{ formatDate(reply.get("createdAt")) }}
                    </span>
                    <Dropdown
                      :options="commentOptions"
                      placement="right"
                      class="ml-auto"
                    >
                      <Button
                        size="sm"
                        variant="ghost"
                        icon="more-horizontal"
                      />
                    </Dropdown>
                  </div>
                  <div class="pl-10 -mt-1.5 text-sm leading-5">
                    <span class="max-w-full break-word text-gray-700">
                      {{ reply.get("content") }}
                    </span>
                  </div>
                </div>

                <section
                  v-if="comment.get('id') === activeCommentID"
                  class="flex flex-col gap-2 mt-3 py-3"
                >
                  <div class="flex items-center justify-start gap-2">
                    <Avatar
                      size="lg"
                      :label="fullName"
                      :image="imageURL"
                      class=""
                    />
                    <div
                      class="flex items-center w-full border rounded pr-2 hover:bg-gray-100"
                    >
                      <textarea
                        :ref="
                          (el) => {
                            textarea[comment.get('id')] = el
                          }
                        "
                        class="w-full h-7 placeholder-gray-500 max-h-[60vh] overflow-y-hidden form-textarea block bg-transparent border-0 shadow- mx-0.5 resize-none focus:outline-0 focus:border-0 active:outline-0 hover:bg-transparent"
                        v-model="commentText"
                        placeholder="Reply"
                        @input="resize($event)"
                        @keypress.enter.stop.prevent="
                          addReply(comment.get('id'))
                        "
                      ></textarea>
                      <Button
                        class="w-auto"
                        :variant="'ghost'"
                        icon="arrow-up-circle"
                        :disabled="!commentText.length"
                        @click="addReply(comment.get('id'))"
                      ></Button>
                    </div>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { useStore } from "vuex"
import {
  ref,
  watch,
  computed,
  nextTick,
  onUpdated,
  onMounted,
  h,
  inject,
} from "vue"
import { Avatar, Button, Input, Dropdown, FeatherIcon, Dialog } from "frappe-ui"
import { History, PcCaseIcon } from "lucide-vue-next"
import { formatDate } from "@/utils/format"
import { v4 as uuidv4, v4 } from "uuid"
import { useTimeAgo } from "@vueuse/core"
import { Editor } from "@tiptap/vue-3"
import * as Y from "yjs"

const store = useStore()

const emit = defineEmits([
  "setActiveComment",
  /* "update:allComments", */
  "update:activeCommentID",
])

interface Props {
  /* allComments: any[]; */
  activeCommentID: string
  isCommentModeOn: boolean
}
const doc = inject("doc")
const allComments = doc.value.getArray("docAnnotations")
const props = defineProps<Props>()

const commentText = ref<string>("")
const showCommentHistory = ref(false)
const textarea = ref<Record<string, any>>({})

const fullName = computed(() => store.state.user.fullName)
const email = computed(() => store.state.auth.user_id)
const imageURL = computed(() => store.state.user.imageURL)

const addReply = (parentID) => {
  const newID = uuidv4()
  const newReplyYmap = new Y.Map()
  let parent
  for (const value of allComments) {
    if (value.get("id") === parentID) {
      parent = value
      break
    }
  }
  let replies_arr = parent.get("replies")
  newReplyYmap.set("id", newID)
  newReplyYmap.set("content", commentText.value)
  newReplyYmap.set("owner", fullName.value)
  newReplyYmap.set("ownerEmail", email.value)
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
    for (const value of allComments) {
      if (value.id === parentID){
        pval = value
        break
      }
      
     }
 */
  /*     console.log(pval)
    pval.replies.push(newReply) */
  /* let parentComment = props.allComments.find((item) => item.id === parentID);
    if (parentComment && Array.isArray(parentComment.replies)) {
      parentComment.replies.push(newReply);
    } */
  commentText.value = ""
}

const commentOptions = [
  {
    label: "Edit",
    onClick: () => {},
    //icon: () => h(FeatherIcon, { name: "edit-2" }),
  },
  {
    label: "Resolve",
    onClick: () => {},
    //icon: () => h(FeatherIcon, { name: "edit-2" }),
  },
  {
    label: "Delete",
    onClick: () => {
      console.log(props.allComments)
    },
    //icon: () => h(FeatherIcon, { name: "trash-2" }),
  },
]

const enabledComments = computed(() => {
  let arr = allComments.toArray()
  return arr.filter((item) => item.get("anchor") === 1)
})

const disabledComments = computed(() => {
  let arr = allComments.toArray()
  return arr.filter((item) => item.get("anchor") === 0)
})
/*   
  watch(props.activeCommentID, (val) => {
    console.log(val);
    console.log("FOCUS REF HERE");
    setTimeout(() => {
      if (!val || !props.isCommentModeOn) return;
      commentText.value = "";
  
      const activeTextArea: HTMLTextAreaElement = textarea.value[val];
  
      if (activeTextArea) activeTextArea.focus();
    }, 100); 
  }); */

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

<style>
.current-comment {
  transition: all 0.25s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.slide-fade-enter-active {
  transition: all 0.5s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.slide-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>
