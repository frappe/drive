<template>
  <div class="flex items-center text-base">
    <router-link
      v-for="(item, index) in breadcrumbLinks"
      :key="item.label"
      v-slot="{ href, navigate }"
      class="text-2xl font-medium"
      :class="isLastItem(index) ? 'text-inherit' : 'text-gray-600'"
      :to="item.route">
      <a :href="href" @click="navigate">
        {{ item.label }}
        <span v-if="!isLastItem(index)" class="px-2">{{ ">" }}</span>
      </a>
    </router-link>
  </div>
</template>
<script>
export default {
  name: "Breadcrumbs",
  props: {
    breadcrumbLinks: {
      type: Array,
      required: true,
    },
  },
  methods: {
    isLastItem(index) {
      return index === this.breadcrumbLinks.length - 1;
    },
  },
};
</script>
