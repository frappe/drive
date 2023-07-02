<template>
  <Menu v-if="fixedMenuButtons" :buttons="fixedMenuButtons" />
</template>
<script>
import Menu from "./Menu.vue";
import { createEditorButton } from "./utils";

export default {
  name: "TextEditorFixedMenu",
  components: { Menu },
  inject: ["editor"],
  props: ["buttons"],
  computed: {
    fixedMenuButtons() {
      if (!this.buttons) return false;
      let buttons;
      if (Array.isArray(this.buttons)) {
        buttons = this.buttons;
      } else {
        buttons = [
          "Undo",
          "Redo",
          "Separator",
          [
            "Heading 1",
            "Heading 2",
            "Heading 3",
            "Heading 4",
            /*      "Heading 5",
            "Heading 6", */
          ],
          "Separator",
          "Bold",
          "Italic",
          "Separator",
          "Bullet List",
          "Numbered List",
          "Separator",
          "Align Left",
          "Align Center",
          "Align Right",
          "Separator",
          "FontColor",
          "Separator",
          ["Sans-serif", "Serif", "Monospace"],
          [
            "line height 100%",
            "line height 115%",
            "line height 150%",
            "line height 200%",
            "line height 250%",
            "line height 300%",
          ],
          "Separator",
          ["text-xs", "text-sm", "text-base", "text-lg", "text-xl"],
          "Separator",
          "Image",
          "Video",
          "Link",
          "Blockquote",
          "Code",
          "Horizontal Rule",
          [
            "InsertTable",
            "AddColumnBefore",
            "AddColumnAfter",
            "DeleteColumn",
            "AddRowBefore",
            "AddRowAfter",
            "DeleteRow",
            "MergeCells",
            "SplitCell",
            "ToggleHeaderColumn",
            "ToggleHeaderRow",
            "ToggleHeaderCell",
            "DeleteTable",
          ],
          "Separator",
        ];
      }
      return buttons.map(createEditorButton);
    },
  },
};
</script>
