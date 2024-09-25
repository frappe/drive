<template>
  <div
    class="inline-flex gap-1 items-center justify-center text-gray-800 border hover:bg-gray-200 h-7 px-2 rounded group cursor-pointer"
  >
    <svg
      v-if="entity.owner === 'You' && !allowDelete"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        r="4.5"
        cx="8"
        cy="8"
        :fill="tag.color"
        :stroke="tag.color"
        stroke-width="3"
      />
    </svg>

    <span class="text-sm text-gray-800">
      {{ tag.title }}
    </span>
    <button
      v-if="entity.owner === 'You' && allowDelete"
      icon="x"
      @click="$resources.removeTag.submit()"
    >
      <FeatherIcon class="my-auto h-3.5 w-3.5 stroke-2" name="x" />
    </button>
  </div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
  name: "Tag",

  components: {
    FeatherIcon,
  },

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
