<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Experimental Feature' }"
    :disable-outside-click-to-close="true"
  >
    <template #body-main>
      <div
        class="flex flex-col gap-y-4 bg-white px-4 pb-6 pt-5 sm:px-6 text-gray-800 text-base"
      >
        <div class="mb-2 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-gray-900">
            Experimental Feature
          </h3>
        </div>
        <span
          >This whiteboard is built and powered by
          <a class="underline" href="https://tldraw.dev/">tldraw,</a> and is
          subject to thier
          <a
            class="underline"
            href="https://github.com/tldraw/tldraw/blob/main/LICENSE.md"
            >license</a
          >
          and
          <a
            class="underline"
            href="https://github.com/tldraw/tldraw/blob/main/TRADEMARKS.md"
            >trademark</a
          >.
        </span>

        <span
          >This feature is marked as experimental, and may be removed at any
          time without prior notice</span
        >
        <Checkbox
          v-model="accept"
          label="I understand, don't show this to me again"
        />
      </div>
    </template>
    <template #actions>
      <Button
        :disabled="!accept"
        variant="subtle"
        theme="red"
        class="w-full"
        @click="open = false"
      >
        Confirm
      </Button>
    </template>
  </Dialog>
</template>
<script setup>
import { Button, Dialog } from "frappe-ui"
import Checkbox from "frappe-ui/src/components/Checkbox.vue"
import { computed, ref, watch } from "vue"

const accept = ref(false)
const emit = defineEmits(["update:modelValue"])
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: false,
    default: true,
  },
})

watch(
  () => accept.value,
  (newValue) => {
    localStorage.setItem("tldrawAccepted", newValue)
  }
)

const open = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit("update:modelValue", value)
  },
})
</script>
