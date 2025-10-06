<template>
  <Combobox
    placeholder="Select a team"
    :options
    :disabled
    :open-on-click="true"
    v-model="team"
  />
</template>
<script setup lang="ts">
import { getTeams } from "@/resources/files"
import icons from "@/utils/icons"
import { computed, watch } from "vue"
import { Combobox } from "frappe-ui"
import { DropdownItem } from "frappe-ui/src/components/Dropdown/types"
import { dynamicList } from "@/utils/files"

getTeams.fetch()
const team = defineModel<string>()
const props = defineProps({
  none: { default: false, type: Boolean || String },
  allowBlank: { default: false },
  disabled: { default: false },
})
watch(
  getTeams.data,
  (teams) => {
    if (!Object.values(teams || {}).length || props.allowBlank || team.value)
      return
    if (props.none) {
      team.value = props.none === true ? "all" : "home"
    } else {
      team.value = Object.values(teams)[0]?.name
    }
  },
  { immediate: true }
)
const options = computed<DropdownItem[]>(() => {
  const res = Object.values(getTeams.data).map((k) => ({
    label: k.title,
    value: k.name,
    icon: icons[k.icon || "building"],
  }))
  return dynamicList([
    { cond: props.none === true, label: "Everywhere", value: "all" },
    { cond: props.none, label: "Home", value: "home" },
    ...res,
  ])
})
</script>
