<script setup>
import { reactive, onMounted, ref, toRaw, watchEffect } from "vue"

const slots = defineSlots()
const initialValues = reactive({})

const getKey = (input) => input.props.label || input.props.id

const addToInitial = (inputs) => {
  for (const input of inputs) {
    if (input?.props && "modelValue" in input.props && getKey(input)) {
      initialValues[getKey(input)] = toRaw(input.props.modelValue)
    }
    if (input?.type === "div") {
      addToInitial(input.children)
    }
  }
}

const checkChanges = (inputs) => {
  let dirty = false
  error.value = null
  for (const input of inputs) {
    if (input?.props && "modelValue" in input.props) {
      const initial = initialValues[getKey(input)]
      if (toRaw(input.props.modelValue) !== initial) dirty = true
      if (!error.value) {
        const message = input.props.validate?.(input.props.modelValue)
        if (message !== true) error.value = message
      }
    }
    if (!dirty && input?.type === "div") {
      dirty = checkChanges(input.children)
    }
  }
  return dirty
}
onMounted(() => {
  const inputs = slots.default?.(false) || []
  addToInitial(inputs)
})
const dirty = ref(false)
const error = ref(undefined)
watchEffect(() => {
  const inputs = slots.default?.(false) || []
  dirty.value = checkChanges(inputs)
})
const setDirty = (val) => (dirty.value = val)
</script>

<template>
  <slot
    :dirty
    :set-dirty
    :error
  />
</template>
