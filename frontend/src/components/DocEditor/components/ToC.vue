<template>
  <div class="hidden md:flex right-3 absolute pt-3">
    <div
      v-show="show"
      class="p-3 table-of-contents bg-white shadow-sm rounded-sm"
    >
      <div
        v-for="anchor in anchors"
        :key="anchor.id"
        class="hover:bg-surface-gray-2"
        :class="{
          'is-active': anchor.isActive && !anchor.isScrolledOver,
          'text-ink-gray-5': anchor.isScrolledOver,
        }"
        :style="{ '--level': anchor.level - maxLevel }"
      >
        <a
          :href="'#' + anchor.id"
          class="text-sm px-0.5"
          :title="anchor.textContent"
          @click.prevent="onAnchorClick(anchor.id)"
          :data-item-index="anchor.itemIndex"
        >
          <span class="max-w-40 truncate">{{ anchor.textContent }}</span>
        </a>
      </div>
    </div>
    <Button
      variant="ghost"
      :tooltip="show ? 'Hide' : 'Table of Contents'"
      class="!w-5.5 !h-5.5 mr-1.5 ml-1"
      @click="show = !show"
    >
      <template #icon>
        <component
          :is="show ? LucideMinus : LucideTableOfContents"
          class="size-4"
      /></template>
    </Button>
  </div>
</template>

<script setup>
import { TextSelection } from "@tiptap/pm/state"
import LucideMinus from "~icons/lucide/minus"
import LucidePlus from "~icons/lucide/plus"
import LucideTableOfContents from "~icons/lucide/table-of-contents"
import { ref, watch, computed } from "vue"
import { LucideList } from "lucide-vue-next"

const props = defineProps({
  editor: Object,
  anchors: {
    type: Array,
    default: [],
  },
})
const show = ref(JSON.parse(localStorage.getItem("showToc") || false))
watch(show, (v) => localStorage.setItem("showToc", v))

const maxLevel = computed(
  () => Math.min(...props.anchors.map((k) => k.level)) - 1
)
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

  const editorEl = props.editor.options.element.parentElement
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
  text-decoration: none;

  &::before {
    content: "";
  }
}

.table-of-contents > div {
  border-radius: 0.25rem;
  padding-left: calc(0.875rem * (var(--level) - 1));
  transition: all 0.2s cubic-bezier(0.65, 0.05, 0.36, 1);
}
</style>
