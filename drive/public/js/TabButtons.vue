<template>
  <div>
    <button
      v-for="(tab, idx) in tabs"
      :key="tab.label"
      @click="$emit('update:modelValue', idx)"
      :class="{ active: idx === modelValue }"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
<script setup>
import { version } from "vue";
defineProps({
  tabs: Array,
  modelValue: Number,
});

defineEmits(["update:modelValue"]);
</script>
<style scoped>
div {
  border-radius: 0.625rem;
  height: 1.75rem;
  width: fit-content;
  align-items: center;
  display: flex;
  font-size: 13px;
  line-height: 1.15;
  letter-spacing: 0.02em;
  font-weight: 420;
  background: #f3f3f3;
  padding: 0 1px;
  gap: 0.125rem;
}

button {
  flex-shrink: 0;
  background: #f3f3f3;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  height: 1.625rem !important;
  border-radius: 0.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
}

button.active {
  background: white;
  box-shadow: 0 0 #0000, 0 0 #0000, 0px 0px 1px rgba(0, 0, 0, 0.45),
    0px 1px 2px rgba(0, 0, 0, 0.1);
}
</style>
