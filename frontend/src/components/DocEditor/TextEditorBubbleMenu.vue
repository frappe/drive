<template>
  <BubbleMenu
    v-if="bubbleMenuButtons"
    class="bubble-menu rounded-md shadow-sm"
    :tippy-options="{ duration: 100 }"
    :editor="editor">
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
  props: ["buttons"],
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
          "Paragraph",
          "Heading 1",
          "Heading 2",
          "Heading 3",
          "Separator",
          "Bold",
          "Italic",
          "Strikethrough",
          "Link",
        ];
      }
      return buttons.map(createEditorButton);
    },
  },
};
</script>
