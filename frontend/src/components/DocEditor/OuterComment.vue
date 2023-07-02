<template>
  <section class="text-base float-right w-3/12 flex flex-col gap-2">
    <article
      v-for="(comment, i) in allComments"
      :key="i + ''"
      class="bg-white shadow-sm rounded-md border flex flex-col gap-2 mb-8 p-2 pb-0"
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
        class="border-b py-2 px-2 pb-6">
        <div class="flex justify-start items-center mb-2">
          <Avatar class="mr-2" :label="jsonComment.userName" />
          <div class="">
            <span class="text-sm font-semibold">
              {{ jsonComment.userName }}
            </span>
            <br />
            <span class="text-sm text-slate-600">
              {{ formatDate(jsonComment.time) }}
            </span>
          </div>
        </div>

        <p class="pl-1">{{ jsonComment.content }}</p>
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
        <Input
          :ref="
            (el) => {
              textareaRefs[comment.jsonComments.uuid] = el;
            }
          "
          v-model="commentText"
          placeholder="Add comment..."
          @keypress.enter.stop.prevent="setComment" />

        <section class="flex flex-row gap-2 justify-end">
          <Button appearance="primary" @click="setComment">Add</Button>
        </section>
      </section>
    </article>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Avatar, Button, Input } from "frappe-ui";
import { formatDate } from "@/utils/format";

const emit = defineEmits(["setComment"]);

interface Props {
  allComments: any[];
  activeCommentsInstance: {
    uuid: "";
    comments: [];
  };
  focusContent: ({ from, to }: { from: number; to: number }) => void;
  /* formatDate: (d: any) => string | null */
}

const props = defineProps<Props>();

const commentText = ref<string>("");

const textareaRefs = ref<Record<string, any>>({});

const activeCommentInstanceUuid = computed(
  () => props.activeCommentsInstance.uuid
);

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
