<template>
  <GenericPage
    :get-entities="getPersonal"
    :icon="LucideHome"
    primary-message="Thư mục cá nhân trống"
    :verify="{
      data: {
        write: 1,
      },
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getPersonal } from "@/resources/files"
import { useStore } from "vuex"
import LucideHome from "~icons/lucide/home"

const store = useStore()
store.commit("setCurrentFolder", { name: "" })
</script>
