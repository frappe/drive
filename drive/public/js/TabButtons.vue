<template>
  <div class="dropdown">
    <button
      class="dropdown-toggle"
      v-html="filterIcon"
      data-toggle="dropdown"
    />

    <div class="dropdown-menu dropdown-menu-right">
      <div
        v-for="tab in tabs"
        class="dropdown-item"
        @click="$emit('update:modelValue', tab)"
      >
        {{ tab.label }}
        <div
          v-if="modelValue?.label === tab.label"
          v-html="tickIcon"
          style="display: flex"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tabs: Array,
  modelValue: Object,
});
const filterIcon = frappe.utils.icon("filter", "md");
const tickIcon = frappe.utils.icon("tick", "sm");
defineEmits(["update:modelValue"]);
</script>

<style scoped>
.dropdown {
  position: relative;
  display: inline-block;
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

.dropdown-toggle:focus {
  outline: none;
}
.dropdown-toggle::after {
  content: none;
}

.dropdown-menu {
  left: 0;
  margin-top: 4px;
  border-radius: 4px;
  min-width: 150px;
}

.dropdown-item {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 1.75rem;
  width: 100%;
  border-radius: 0.25rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  line-height: 1.5rem;
}

.dropdown-item:hover {
  background: #f0f0f0;
  color: black !important;
}

.dropdown-item:active {
  background: #f0f0f0;
  color: black !important;
}
</style>
