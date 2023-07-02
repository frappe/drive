<!-- <template>
  <BubbleMenu
    v-if="bubbleMenuButtons"
    class="bubble-menu rounded-md shadow-sm border border-gray-100"
    :tippy-options="{ duration: 100 }"
    :editor="editor"
    >
    <Menu
      class="bg-gray-900"
      :buttons="bubbleMenuButtons" 
    />
  </BubbleMenu>
</template>
<script>
import { BubbleMenu } from "@tiptap/vue-3";
import { createEditorButton } from "./utils";
import Menu from "./Menu.vue";

export default {
  name: "TextEditorBubbleMenu",
  props: ['buttons', 'options'],
  components: { BubbleMenu, Menu },
  inject: ["editor"],
  computed: {
    bubbleMenuButtons() {
      let buttons;
        buttons = [
          ["Heading 1",
        "Heading 2",],
          "Link",
          "Separator",
          "Bold",
          "Italic",
          "Underline",
          "Separator"          
        ];
      return buttons.map(createEditorButton);
    },
  },
};
</script> -->

<template>
  <BubbleMenu
    v-if="bubbleMenuButtons"
    class="bubble-menu rounded-md"
    :tippy-options="{ duration: 100 }"
    :editor="editor"
    v-bind="options">
    <Menu
      class="rounded-md border border-gray-100 shadow-lg"
      :buttons="bubbleMenuButtons" />
  </BubbleMenu>
</template>
<script>
import { BubbleMenu } from "@tiptap/vue-3";
import { createEditorButton } from "./utils";
import Menu from "./Menu.vue";

export default {
  name: "TextEditorBubbleMenu",
  props: ["buttons", "options"],
  components: { BubbleMenu, Menu },
  inject: ["editor"],
  computed: {
    bubbleMenuButtons() {
      if (!this.buttons) return false;

      let buttons;
      if (Array.isArray(this.buttons)) {
        buttons = this.buttons;
      } else {
        buttons = [
          "Link",
          "Separator",
          "Bold",
          "Italic",
          "Underline",
          "Strikethrough",
          "Separator",
          "CommentMode",
        ];
      }
      return buttons.map(createEditorButton);
    },
  },
};
</script>
