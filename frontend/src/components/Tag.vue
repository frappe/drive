<template>
  <div
    class="inline-flex gap-2 items-center text-ink-gray-8 border h-6 px-1 rounded group"
  >
    <div class="flex gap-1 items-center">
      <svg
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          r="2.5"
          cx="6"
          cy="6"
          :fill="tag.color"
          :stroke="tag.color"
          stroke-width="3"
        />
      </svg>

      <span class="text-sm text-ink-gray-8">
        {{ tag.title }}
      </span>
    </div>
    <button
      v-if="entity.write"
      icon="x"
      @click="$resources.removeTag.submit()"
    >
      <LucideX class="my-auto size-3" />
    </button>
  </div>
</template>

<script>
export default {
  name: "Tag",
  props: {
    entity: {
      type: Object,
      required: true,
      default: null,
    },
    allowDelete: {
      type: Boolean,
      required: true,
      default: false,
    },
    tag: {
      type: Object,
      required: true,
      default: null,
    },
  },

  emits: ["success"],

  data() {
    return {
      colors: ["gray", "blue", "green", "orange", "red"],
      tagActions: [
        {
          label: "Delete",
          icon: "trash-2",
          handler: () => {
            this.$resources.deleteTag.submit()
          },
        },
      ],
    }
  },

  resources: {
    updateColor() {
      return {
        url: "drive.api.tags.update_tag_color",
        onSuccess() {
          this.$emit("success")
        },
      }
    },

    removeTag() {
      return {
        url: "drive.api.tags.remove_tag",
        params: {
          entity: this.entity.name,
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success")
        },
      }
    },

    deleteTag() {
      return {
        url: "drive.api.tags.delete_tag",
        params: {
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success")
        },
      }
    },
  },
}
</script>
