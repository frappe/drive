<template>
  <div v-if="node" class="tree-node" :class="{ opened: node.open }">
    <span
      ref="reference"
      class="tree-link"
      @click="emit('node-click', node)"
      style="width: 100%"
      :class="{ active: node.value === selected_node?.value }"
      :disabled="node.fetching"
      @mouseover="onMouseover"
      @mouseleave="onMouseleave"
    >
      <div v-if="icon" v-html="icon" />
      <Thumbnail v-else :node="node" />
      <a class="tree-label text-nowrap overflow-hidden" :title="node.label">{{
        node.label
      }}</a>
      <a
        v-if="!node.is_group"
        :href="'/drive/f/' + node.value"
        class="ml-3 file-link"
        style="align-self: center"
        target="_blank"
        v-html="linkIcon"
      />
      <div
        v-if="node.value === selected_node?.value"
        v-html="checkIcon"
        class="ml-auto"
      />
    </span>
    <div v-if="node.file_url && frappe.utils.is_image_file(node.file_url)">
      <div v-show="isOpen" class="popover" ref="popover" role="tooltip">
        <img :src="node.file_url" />
      </div>
    </div>
    <ul class="tree-children" v-show="node.open">
      <TreeNode
        v-for="n in node.children"
        :key="n.value"
        :node="n"
        :selected_node="selected_node"
        @node-click="(n) => emit('node-click', n)"
        @load-more="(n) => emit('load-more', n)"
      />
      <button
        class="btn btn-xs btn-load-more"
        v-if="node.has_more_children"
        @click="emit('load-more', node)"
        :disabled="node.children_loading"
      >
        {{ node.children_loading ? __("Loading...") : __("Load more") }}
      </button>
    </ul>
  </div>
</template>

<script setup>
import { createPopper } from "@popperjs/core";
import { ref, computed } from "vue";
import Thumbnail from "./Thumbnail.vue";

// props
const props = defineProps({
  node: Object,
  selected_node: { type: Object, required: false },
});

// emits
let emit = defineEmits(["node-click", "load-more"]);

// computed

let linkIcon = frappe.utils.icon("external-link", "sm");
let checkIcon = frappe.utils.icon("tick", "sm", "", "", "check-icon");
let icon = computed(() => {
  if (!props.node.is_group) return;

  if (props.node.open) return frappe.utils.icon("folder-open", "sm");
  return frappe.utils.icon("folder-normal", "sm");
});

const reference = ref(null);
const popover = ref(null);
let isOpen = ref(false);

let popper = ref(null);

function setupPopper() {
  if (!popper.value) {
    popper.value = createPopper(reference.value, popover.value, {
      placement: "top",
      modifiers: [
        {
          name: "offset",
          options: {
            offset: [0, 4],
          },
        },
      ],
    });
  } else {
    popper.value.update();
  }
}

let hoverTimer = null;
let leaveTimer = null;

function onMouseover() {
  leaveTimer && clearTimeout(leaveTimer) && (leaveTimer = null);
  hoverTimer && clearTimeout(hoverTimer);
  hoverTimer = setTimeout(() => {
    isOpen.value = true;
    setupPopper();
  }, 800);
}
function onMouseleave() {
  hoverTimer && clearTimeout(hoverTimer) && (hoverTimer = null);
  leaveTimer && clearTimeout(leaveTimer);
  leaveTimer = setTimeout(() => {
    isOpen.value = false;
  }, 100);
}
</script>

<style scoped>
.btn-load-more {
  margin-left: 1.6rem;
  margin-top: 0.5rem;
}

.popover {
  padding: 10px;
}
.tree-label {
  user-select: none;
  max-width: 300px;
  text-overflow: ellipsis;
}

.tree-link .file-link {
  opacity: 0;
}

.tree-link:hover .file-link {
  opacity: 0.4;
}

.tree-link .file-doc-link:hover {
  opacity: 0.8;
}
.check-icon {
  stroke: white;
  background: black;
  border-radius: 100%;
  padding: 3.5px;
}
</style>
