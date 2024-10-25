<template>
  <div
    class="flex items-center justify-center bg-white shadow-lg rounded-[0.45rem] gap-x-1 px-0.5 py-0.5"
  >
    <template v-for="button in buttons" :key="button.label">
      <div v-if="button.type === 'separator'" class="h-5 border-l"></div>
      <component :is="button.component || 'div'" v-else v-bind="{ editor }">
        <template #default="componentSlotProps">
          <div
            v-if="button.label === 'New Link' && button.isActive(editor)"
            class="flex items-center justify-start"
          >
            <a
              class="text-gray-800 text-sm underline hover:bg-gray-100 rounded-[0.35rem] px-1 py-0.5 gap-x-1 line-clamp-1 max-w-44"
              :href="editor.getAttributes('link').href"
              :title="editor.getAttributes('link').href"
              target="_blank"
            >
              {{ editor.getAttributes("link").href }}</a
            >
            <button
              class="hover:bg-gray-100 text-gray-800 rounded-[0.35rem] p-1"
            >
              <Edit2
                class="h-3.5 w-auto stroke-[1.5]"
                title="Edit Link"
                @click="componentSlotProps.onClick(button)"
              />
            </button>
          </div>
          <button
            v-else
            class="flex items-center rounded-[0.35rem] p-1 text-gray-800 transition-colors gap-1"
            :class="
              button.isActive(editor) || componentSlotProps?.isActive
                ? 'bg-gray-200 text-gray-400'
                : 'hover:bg-gray-100'
            "
            :title="button.label"
            @click="
              componentSlotProps?.onClick
                ? componentSlotProps.onClick(button)
                : onButtonClick(button)
            "
          >
            <component
              :is="button.icon"
              v-if="button.icon"
              class="h-4 w-auto stroke-[1.5]"
            />
            <span
              v-else
              class="inline-block h-4 min-w-[1rem] text-sm leading-4"
            >
              {{ button.text }}
            </span>
          </button>
        </template>
      </component>
    </template>
  </div>
</template>
<script>
import { Popover, FeatherIcon } from "frappe-ui"
import { Edit2, Unlink2 } from "lucide-vue-next"

export default {
  name: "TipTapMenu",
  components: {
    Popover,
    FeatherIcon,
    Unlink2,
    Edit2,
  },
  inject: ["editor"],
  props: ["buttons"],
  emits: ["toggleCommentMode"],

  methods: {
    getLinkFromSelection(editor) {
      const { state } = editor
      const { from, to } = state.selection
      const linkAttributes = []
      state.doc.nodesBetween(from, to, (node) => {
        if (node.isText) {
          node.marks.forEach((mark) => {
            if (mark.type.name === "link") {
              linkAttributes.push(mark.attrs)
            }
          })
        }
      })
      const link = linkAttributes.length > 0 ? linkAttributes[0].href : null

      return link
    },
    onButtonClick(button) {
      if (typeof button.action === "string") {
        this.emitter.emit(button.action)
      } else {
        button.action(this.editor)
      }
    },
  },
}
</script>
