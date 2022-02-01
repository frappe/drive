<template>
  <div class="text-gray-900">
    <div class="h-screen" :class="{ 'sm:bg-gray-50': $route.meta.isLoginPage }">
      <router-view />
    </div>
  </div>
</template>
