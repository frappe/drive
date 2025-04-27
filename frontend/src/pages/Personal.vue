<template>
  <GenericPage
    :getEntities="getPersonal"
    :icon="Home"
    :primaryMessage="'No personal files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Home from "../components/EspressoIcons/Home.vue"
import { getPersonal } from "@/resources/files"
import { useStore } from "vuex"

const store = useStore()
store.commit("setCurrentFolder", "")
store.commit("setCurrentFolderID", "")
</script>
