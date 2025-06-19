<template>
  <div
    ref="scrollContainer"
    class="flex w-44 flex-col rounded-md border bg-surface-white p-1.5 text-base shadow gap-y-0.5 overflow-y-auto"
  >
    <template v-if="enabledItems.length">
      <div
        v-for="(item, index) in enabledItems"
        :key="index"
      >
        <span
          v-if="item.type"
          class="flex w-full p-1 text-sm font-medium text-ink-gray-5"
          >{{ item.title }}</span
        >
        <button
          v-else
          class="flex h-7 w-full cursor-pointer items-center rounded-[0.4rem] px-1 text-base"
          :class="{ 'bg-surface-gray-2': index === selectedIndex }"
          @click="selectItem(index)"
          @mouseenter="selectedIndex = index"
        >
          <component
            :is="item.icon"
            class="mr-2 size-4 text-ink-gray-5"
          />
          {{ item.title }}
          <component
            :is="item.component"
            v-if="item.component"
            :editor="editor"
            :is-open="item.isOpen"
            @toggle-is-open="toggleIsOpen(item)"
          >
            {{ item.title }}
          </component>
        </button>
      </div>
    </template>
    <div
      v-else
      class="item"
    >
      No result
    </div>
  </div>
</template>

<script>
import Minus from "~icons/lucide/minus"

export default {
  components: {
    Minus,
  },
  props: {
    items: {
      type: Array,
      required: true,
    },

    editor: {
      type: Object,
      required: true,
    },

    command: {
      type: Function,
      required: true,
    },
  },

  data() {
    return {
      selectedIndex: 0,
    }
  },

  computed: {
    enabledItems() {
      return this.items.filter((item) =>
        item.disabled ? !item.disabled(this.editor) : true
      )
    },
  },

  watch: {
    items() {
      this.selectedIndex = 0
    },
  },

  methods: {
    toggleIsOpen(item) {
      item.isOpen = !item.isOpen
    },

    onKeyDown({ event }) {
      if (event.key === "ArrowUp") {
        this.upHandler()
        return true
      }

      if (event.key === "ArrowDown") {
        this.downHandler()
        return true
      }

      if (event.key === "Enter") {
        this.enterHandler()
        return true
      }

      return false
    },

    upHandler() {
      this.selectedIndex =
        (this.selectedIndex + this.enabledItems.length - 1) %
        this.enabledItems.length
    },

    downHandler() {
      this.selectedIndex = (this.selectedIndex + 1) % this.enabledItems.length
    },

    enterHandler() {
      this.selectItem(this.selectedIndex)
    },

    selectItem(index) {
      const item = this.enabledItems[index]

      if (item.command) {
        this.command(item)
      } else if (item.component) {
        item.isOpen = true
      }
    },
  },
}
</script>
