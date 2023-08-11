<template>
  <section class="text-base float-right w-full flex flex-col">
    <article
      v-for="(comment, i) in allComments"
      :key="i + ''"
      class="current-comment bg-white flex flex-col border-b last:border-b-0 pt-4"
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
        class="my-2">
        <div class="mb-2 flex gap-3 items-center">
          <!--           <Avatar class="mr-2" :label="jsonComment.userName" />
 -->
          <Avatar
            :label="jsonComment.userName"
            :image="jsonComment.userImage"
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
        class="flex flex-col"
        :class="[
          `${
            comment.jsonComments.uuid === activeCommentsInstance.uuid
              ? 'border-blue-900'
              : 'max-h-0 border-blue-300'
          }`,
        ]">
        <div class="flex items-center gap-3 mt-2 mb-4">
          <Avatar :label="fullName" :image="imageURL" class="h-7 w-7" />
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

          <Button variant="solid" @click="setComment">Add</Button>
        </div>
      </section>
    </article>
  </section>
</template>

<script setup lang="ts">
import { useStore } from "vuex";
import { ref, watch, computed } from "vue";
import { Avatar, Button, Input } from "frappe-ui";
import { formatDate } from "@/utils/format";

const store = useStore();

const emit = defineEmits(["setComment"]);

interface Props {
  allComments: any[];
  activeCommentsInstance: {
    uuid: "";
    comments: [];
  };
  focusContent: ({ from, to }: { from: number; to: number }) => void;
}

const props = defineProps<Props>();

const commentText = ref<string>("");

const textareaRefs = ref<Record<string, any>>({});

const activeCommentInstanceUuid = computed(
  () => props.activeCommentsInstance.uuid
);

const fullName = computed(() => store.state.user.fullName);

const imageURL = computed(() => store.state.user.imageURL);

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
  transition: all 0.15s ease-in-out;

  &.active {
    padding-top: 15px;
    padding-bottom: 15px;
  }
}
</style>
