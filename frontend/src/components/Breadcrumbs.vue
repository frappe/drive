<template>
  <div class="flex justify-items-center items-center text-base">
    <div class="flex text-md line-clamp-1 sm:text-lg font-medium">
      <template
        v-for="(item, index) in $store.state.breadcrumbs"
        :key="item.label"
      >
        <router-link
          v-if="index !== $store.state.breadcrumbs.length - 1"
          class="text-gray-600 hover:text-gray-800"
          :to="item.route"
        >
          <span> {{ item.label }}</span>
          <span class="mx-1">/</span>
        </router-link>
        <span v-else class="text-black">
          {{ item.label }}
        </span>
      </template>
    </div>
  </div>
</template>
