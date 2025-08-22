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
      <div v-html="icon" />
      <a
        class="tree-label text-nowrap overflow-hidden"
        :title="node.label"
        style="max-width: 120px; text-overflow: ellipsis"
        >{{ node.label }}</a
      >
      <a
        v-if="!node.is_group"
        :href="'/drive/f/' + node.value"
        class="ml-auto file-link"
        target="_blank"
        v-html="linkIcon"
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

// props
const props = defineProps({
  node: Object,
  selected_node: Object,
});

// emits
let emit = defineEmits(["node-click", "load-more"]);

// computed

let linkIcon = frappe.utils.icon("external-link", "sm");
let icon = computed(() => {
  let icons = {
    open: frappe.utils.icon("folder-open", "xs"),
    closed: frappe.utils.icon("folder-normal", "xs"),
    file: frappe.utils.icon("small-file", "xs"),
    link: frappe.utils.icon("link", "xs"),
    doc: frappe.utils.icon("file", "xs"),
    image: frappe.utils.icon("image", "xs"),
    search: frappe.utils.icon("search"),
  };

  if (props.node.by_search) return icons.search;
  if (props.node.is_group && props.node.open) return icons.open;
  if (props.node.is_group) return icons.closed;
  if (props.node.document) return icons.doc;
  if (props.node.is_link) return icons.link;
  if (props.node.mime_type?.startsWith?.("image")) return icons.image;
  return icons.file;
});

let open_file = (filename) => {
  return frappe.utils.get_form_link("File", filename);
};

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

.tree-link .file-link {
  opacity: 0;
}

.tree-link:hover .file-link {
  opacity: 0.4;
}

.tree-link .file-doc-link:hover {
  opacity: 0.8;
}
</style>
