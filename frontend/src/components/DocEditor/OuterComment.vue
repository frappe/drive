<template>
  <section class="text-base float-right w-full flex flex-col">
    <article
      v-for="(comment, i) in allComments"
      :key="i + ''"
      class="current-comment bg-white flex flex-col border-b"
      :class="[
        `${
          comment.jsonComments.uuid === activeCommentsInstance.uuid
            ? 'active'
            : 'cursor-pointer'
        }`,
      ]"
      @click.stop.prevent="
        focusContent({ from: comment.from, to: comment.to })
      ">
      <div
        v-for="(jsonComment, j) in comment.jsonComments.comments"
        :key="`${j}_${Math.random()}`"
        class="my-4">
        <div class="mb-2 flex gap-3 items-center">
          <!--           <Avatar class="mr-2" :label="jsonComment.userName" />
 -->
          <Avatar
            :label="jsonComment.userName"
            :image-u-r-l="jsonComment.user_image"
            class="h-7 w-7" />
          <div>
            <span class="my-1">
              <span class="text-sm font-medium">
                {{ jsonComment.userName }}
              </span>
              <span class="text-gray-500 text-sm">{{ " ∙ " }}</span>
              <span class="text-gray-700 text-sm">
                {{ formatDate(jsonComment.time) }}
              </span>
            </span>
            <div class="text-base text-gray-700">
              {{ jsonComment.content }}
            </div>
          </div>
        </div>
      </div>

      <section
        v-if="comment.jsonComments.uuid === activeCommentsInstance.uuid"
        class="flex flex-col gap-2 pb-2"
        :class="[
          `${
            comment.jsonComments.uuid === activeCommentsInstance.uuid
              ? 'border-blue-900'
              : 'max-h-0 border-blue-300'
          }`,
        ]">
        <div class="flex items-center gap-3">
          <Avatar label="Admin" class="h-7 w-7" />
          <textarea
            :ref="
              (el) => {
                textareaRefs[comment.jsonComments.uuid] = el;
              }
            "
            class="placeholder-gray-500 max-h-8 form-textarea block w-full resize-none"
            v-model="commentText"
            placeholder="Add comment..."
            @keypress.enter.stop.prevent="setComment" />
          <!-- <Input
                      v-model="newComment"
                      type="text"
                      class="border-gray-400 placeholder-gray-500 w-full grow bg-white focus:bg-white"
                      placeholder="Add comment"
                      @keydown.enter="postComment" /> -->
          <Button appearance="primary" @click="setComment">Add</Button>
        </div>
      </section>
    </article>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Avatar, Button, Input } from "frappe-ui";
import { formatDate } from "@/utils/format";

const emit = defineEmits(["setComment", "focusContent"]);

interface Props {
  allComments: any[];
  activeCommentsInstance: {
    uuid: "";
    comments: [];
  };
  /* focusContent: ({ from, to }: { from: number; to: number }) => void; */
  /* formatDate: (d: any) => string | null */
}

const props = defineProps<Props>();

const commentText = ref<string>("");

const textareaRefs = ref<Record<string, any>>({});

const activeCommentInstanceUuid = computed(
  () => props.activeCommentsInstance.uuid
);

const focusContent = (val) => {
  emit("focusContent", val);
};

const setComment = () => {
  emit("setComment", commentText.value);
  commentText.value = "";
};

watch(activeCommentInstanceUuid, (val) => {
  setTimeout(() => {
    if (!val /* || !props.isCommentModeOn */) return;

    const activeTextArea: HTMLTextAreaElement = textareaRefs.value[val];

    /* if (activeTextArea) activeTextArea.focus() */
  }, 100);
});
</script>

<style lang="scss">
.current-comment {
  transition: all 0.05s;

  &.active {
    padding-top: 45px;
    padding-bottom: 45px;
  }
}
</style>
