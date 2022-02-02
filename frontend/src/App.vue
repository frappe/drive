<template>
  <div class="text-gray-900 flex h-screen overflow-hidden">
    <div
      class="flex flex-1 overflow-y-auto"
      :class="{ 'sm:bg-gray-50': $route.meta.isLoginPage }"
    >
      <div class="flex-1">
        <router-view />
      </div>
    </div>
  </div>
</template>
