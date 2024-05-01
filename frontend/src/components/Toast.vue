<template>
  <div
    class="my-2 min-w-[15rem] max-w-[45rem] rounded-md border bg-white p-3 shadow-[0_4px_12px_#0000001a]"
  >
    <div class="flex place-items-center">
      <FeatherIcon
        v-if="icon"
        :name="icon"
        :class="['h-4.5 w-4.5 mr-2', iconClasses]"
      />
      <div>
        <slot>
          <p
            v-if="title"
            class="text-base font-medium text-gray-900"
            :class="{ 'mb-1': text }"
          >
            {{ title }}
          </p>
          <p v-if="text" class="text-sm text-gray-600">
            {{ text }}
          </p>
        </slot>
      </div>
      <div class="ml-auto pl-2">
        <slot name="actions">
          <button
            class="grid h-5 w-5 place-items-center rounded hover:bg-gray-100"
            @click="$emit('close')"
          >
            <FeatherIcon name="x" class="h-4 w-4 text-gray-700" />
          </button>
        </slot>
      </div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui"

export default {
  name: "Toast",
  components: {
    FeatherIcon,
  },
  props: {
    position: {
      type: String,
      default: "top-center",
    },
    icon: {
      type: String,
      default: "",
    },
    iconClasses: {
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
      default: 5,
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
