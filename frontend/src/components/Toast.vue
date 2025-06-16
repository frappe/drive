<template>
  <div
    class="my-2 min-w-[15rem] max-w-[45rem] rounded-md border p-3 shadow-[0_4px_12px_#0000001a]"
    :class="background"
  >
    <div class="flex place-items-center">
      <FeatherIcon
        v-if="icon"
        :name="icon"
        :class="['h-4.5 w-4.5 mr-2', iconClasses]"
      />
      <Avatar
        v-else-if="avatarURL"
        :label="avatarLabel"
        :image="avatarURL"
        size="sm"
        :class="['mr-2']"
      />
      <div>
        <slot>
          <p
            v-if="title"
            class="text-base font-medium text-ink-gray-9"
            :class="{ 'mb-1': text }"
          >
            {{ title }}
          </p>
          <p
            v-if="text"
            class="text-sm text-ink-gray-5"
          >
            {{ text }}
          </p>
          <Button
            v-for="button in buttons"
            class="mt-2"
            @click="button.action(), $emit('close')"
          >
            {{ button.label }}
          </Button>
        </slot>
      </div>
      <div class="ml-auto mb-auto pl-2">
        <slot name="actions">
          <button
            class="grid h-5 w-5 place-items-center rounded hover:bg-surface-gray-2"
            @click="$emit('close')"
          >
            <LucideX class="size-4 text-ink-gray-7" />
          </button>
        </slot>
      </div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon, Avatar } from "frappe-ui"

export default {
  name: "Toast",
  components: {
    FeatherIcon,
    Avatar,
  },
  props: {
    background: {
      type: String,
      default: "bg-surface-white",
    },
    buttons: {
      type: Array,
    },
    position: {
      type: String,
      default: "bottom-right",
    },
    icon: {
      type: String,
      default: "",
    },
    iconClasses: {
      type: String,
      default: "",
    },
    avatarURL: {
      type: String,
      default: "",
    },
    avatarLabel: {
      type: String,
      default: "",
    },
    title: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      default: "",
    },
    timeout: {
      type: Number,
      default: 10,
    },
  },
  emits: ["close"],
  mounted() {
    if (this.timeout > 0) {
      setTimeout(() => {
        this.$emit("close")
      }, this.timeout * 1000)
    }
  },
}
</script>
