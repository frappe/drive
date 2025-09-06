<script setup>
import { reactive, onMounted, computed, toRaw } from "vue"

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

const isDirty = computed(() => {
  const inputs = slots.default?.(false) || []
  let dirty = false
  for (const input of inputs) {
    if (input?.props && "modelValue" in input.props) {
      const initial = initialValues[getKey(input)]
      console.log(toRaw(input.props.modelValue))
      if (toRaw(input.props.modelValue) !== initial) {
        dirty = true
      }
    }
  }
  console.log(dirty)
  return dirty
})
</script>

<template>
  <slot :dirty="isDirty" />
</template>
