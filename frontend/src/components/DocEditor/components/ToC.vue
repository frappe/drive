<template>
  <div
    class="hidden md:flex"
    :class="{ 'absolute right-0': !show }"
  >
    <div
      v-show="show"
      class="pt-6 ps-6 table-of-contents"
    >
      <div
        v-for="anchor in anchors"
        :key="anchor.id"
        class="hover:bg-surface-gray-2"
        :class="{
          'is-active': anchor.isActive && !anchor.isScrolledOver,
          'text-ink-gray-5': anchor.isScrolledOver,
        }"
        :style="{ '--level': anchor.level }"
      >
        <a
          :href="'#' + anchor.id"
          class="max-w-40 truncate px-2"
          @click.prevent="onAnchorClick(anchor.id)"
          :data-item-index="anchor.itemIndex"
        >
          {{ anchor.textContent }}
        </a>
      </div>
    </div>
    <Button
      variant="ghost"
      :tooltip="show ? 'Hide' : 'Table of Contents'"
      class="!w-5.5 !h-5.5 mr-1.5 mt-1.5"
      @click="show = !show"
    >
      <template #icon>
        <component
          :is="show ? LucideX : LucidePlus"
          class="size-3.5"
      /></template>
    </Button>
  </div>
</template>

<script setup>
import { TextSelection } from "@tiptap/pm/state"
import LucideX from "~icons/lucide/x"
import LucidePlus from "~icons/lucide/plus"
import { ref, watch } from "vue"

const props = defineProps({
  editor: Object,
  anchors: {
    type: Array,
    default: [],
  },
})
const show = ref(JSON.parse(localStorage.getItem("showToc") || false))
watch(show, (v) => localStorage.setItem("showToc", v))
const onAnchorClick = (id) => {
  if (!props.editor) return
  const view = props.editor.view
  const tr = view.state.tr

  const element = view.dom.querySelector(`[data-toc-id="${id}"`)
  const pos = view.posAtDOM(element, 0)
  tr.setSelection(new TextSelection(tr.doc.resolve(pos)))
  props.editor.view.dispatch(tr)
  props.editor.view.focus()
  if (history.pushState) {
    history.pushState(null, null, `#${id}`)
  }

  const editorEl = props.editor.options.element
  editorEl.scrollTo({
    top: element.offsetTop - 10,
    behavior: "smooth",
  })
}
</script>
<style scoped>
.table-of-contents {
  display: flex;
  flex-direction: column;
  font-size: 0.875rem;
  gap: 0.25rem;
  overflow: auto;
  text-decoration: none;
}

a {
  color: var(--black);
  display: flex;
  gap: 0.25rem;
  text-decoration: none;

  &::before {
    content: attr(data-item-index) ".";
  }
}

.table-of-contents > div {
  border-radius: 0.25rem;
  padding-left: calc(0.875rem * (var(--level) - 1));
  transition: all 0.2s cubic-bezier(0.65, 0.05, 0.36, 1);
}
</style>
