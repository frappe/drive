<template>
  <GenericPage
    :get-entities="getPersonal"
    :icon="LucideHome"
    primary-message="No personal files"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getPersonal } from "@/resources/files"
import { LucideHome } from "lucide-vue-next"
import { useStore } from "vuex"

const store = useStore()
store.commit("setCurrentFolder", { name: "" })
</script>
