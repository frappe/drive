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
import { computed } from "vue"
import { Combobox } from "frappe-ui"
import { DropdownItem } from "frappe-ui/src/components/Dropdown/types"
const team = defineModel<string>({ default: "all" })
const props = defineProps({
  none: { default: false },
})
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
