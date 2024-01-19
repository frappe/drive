<template>
  <section class="text-sm w-full flex flex-col overflow-x-hidden min-w-full">
    <article
      v-for="(comment, i) in allComments"
      :key="i + ''"
      class="current-comment pt-2 bg-white flex flex-col border-b last:border-b-0"
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
        <div class="flex gap-2 items-center">
          <Avatar
            :label="jsonComment.userName"
            :image="jsonComment.userImage"
            class="h-7 w-7" />
          <div>
            <span class="text-sm font-medium">
              {{ jsonComment.userName }}
            </span>
            <span class="text-gray-500 text-sm">{{ " ∙ " }}</span>
            <span class="text-gray-700 text-sm">
              {{ formatDate(jsonComment.time) }}
            </span>
          </div>
        </div>
        <div class="ml-2.5 mt-2 text-sm text-gray-700 max-w-full break-word">
          <p class="">{{ jsonComment.content }}</p>
        </div>
      </div>

      <section
        v-show="comment.jsonComments.uuid == activeCommentsInstance.uuid"
        class="flex flex-col"
        :class="[
          `${
            comment.jsonComments.uuid === activeCommentsInstance.uuid
              ? ''
              : 'max-h-0'
          }`,
        ]">
        <div class="flex items-center gap-1 mt-2 mb-4">
          <Avatar :label="fullName" :image="imageURL" class="h-7 w-7 mr-1" />
          <span class="text-sm font-medium">
            {{ fullName }}
          </span>
          <span class="text-gray-500 text-sm">{{ "∙" }}</span>
          <span class="text-gray-700 text-sm">Now</span>
        </div>
        <textarea
          :ref="
            (el) => {
              textarea[comment.jsonComments.uuid] = el;
            }
          "
          class="h-7 placeholder-gray-500 max-h-[60vh] overflow-auto form-textarea block w-full resize-none mb-2"
          v-model="commentText"
          placeholder="Reply"
          @input="resize($event)"
          @focus="comment.jsonComments.uuid === activeCommentsInstance.uuid"
          @keypress.enter.stop.prevent="setComment" />
        <Button
          variant="solid"
          :disabled="!commentText.length"
          @click="setComment">
          Save
        </Button>
      </section>
    </article>
  </section>
</template>

<script setup lang="ts">
import { useStore } from "vuex";
import { ref, watch, computed, nextTick, onUpdated } from "vue";
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
  isCommentModeOn: boolean;
  focusContent: ({ from, to }: { from: number; to: number }) => void;
}

const props = defineProps<Props>();

const commentText = ref<string>("");

const textarea = ref<Record<string, any>>({});

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
    if (!val || !props.isCommentModeOn) return;
    commentText.value = "";

    const activeTextArea: HTMLTextAreaElement = textarea.value[val];

    if (activeTextArea) activeTextArea.focus();
  }, 100);
});

function resize(e) {
  e.target.style.height = `${e.target.scrollHeight}px`;
}

/* watch(commentText, (val) => {
  nextTick(() => {
    console.log(textarea.value.style)
    //textarea.value.style.height = textarea.value.style.scrollHeight + 'px';
  })
}) */
</script>

<style lang="scss">
.current-comment {
  transition: all 0.25s cubic-bezier(0.165, 0.84, 0.44, 1);

  &.active {
    padding-bottom: 50px;
  }
}
</style>
