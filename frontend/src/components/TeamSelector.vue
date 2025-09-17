<template>
  <Combobox
    placeholder="Select a team"
    :options
    v-model="team"
  />
</template>
<script setup lang="ts">
import { getTeams } from "@/resources/files"
import icons from "@/utils/icons"
import { computed, watch } from "vue"
import { Combobox } from "frappe-ui"
import { DropdownItem } from "frappe-ui/src/components/Dropdown/types"

getTeams.fetch()
const team = defineModel<string>()
const props = defineProps({
  none: { default: false },
})
watch(
  getTeams.data,
  (teams) => {
    if (!Object.values(teams || {}).length) return
    team.value = Object.values(teams)[0]?.name
    console.log(team.value)
  },
  { immediate: true }
)
const options = computed<DropdownItem[]>(() => {
  const res = Object.values(getTeams.data).map((k: any) => ({
    label: k.title,
    value: k.name,
    icon: icons[k.icon || "building"],
  }))
  if (!props.none) return res
  else
    return [
      { label: "Everywhere", value: "all" },
      { label: "Home", value: "home" },
      ...res,
    ]
})
</script>
