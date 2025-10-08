<template>
  <GenericPage
    :get-entities="getPersonal"
    :empty="{
      icon: LucideHome,
      title: 'No files yet',
      description: 'Upload to get started!',
    }"
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
import { allUsers } from "@/resources/permissions"
import LucideHome from "~icons/lucide/home"

const store = useStore()
store.commit("setCurrentFolder", { name: "", team: "" })
allUsers.fetch(null)
</script>
