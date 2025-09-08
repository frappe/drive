<script setup>
import { reactive, onMounted, ref, toRaw, watchEffect } from "vue"

const slots = defineSlots()
const initialValues = reactive({})

const getKey = (input) => input.props.label || input.props.id

onMounted(() => {
  const inputs = slots.default?.(false) || []
  for (const input of inputs) {
    if (input?.props && "modelValue" in input.props && getKey(input)) {
      initialValues[getKey(input)] = toRaw(input.props.modelValue)
    }
  }
})
const dirty = ref(false)
watchEffect(() => {
  const inputs = slots.default?.(false) || []
  dirty.value = false
  for (const input of inputs) {
    if (input?.props && "modelValue" in input.props) {
      const initial = initialValues[getKey(input)]
      if (toRaw(input.props.modelValue) !== initial) {
        dirty.value = true
      }
    }
  }
})
const setDirty = (val) => (dirty.value = val)
</script>

<template>
  <slot
    :dirty
    :setDirty
  />
</template>
