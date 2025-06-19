<template>
  <GenericPage
    :grouper="groupByTime"
    :get-entities="getRecents"
    :show-sort="false"
    :icon="LucideClock"
    primary-message="No recent files"
    secondary-message="Try opening something!"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getRecents } from "@/resources/files"
import LucideClock from "~icons/lucide/clock"

function groupByTime(entities) {
  const today = new Date()
  const grouped = {
    Today: [],
    "Earlier this week": [],
    "Earlier this month": [],
    "Earlier this year": [],
    "Older than a year": [],
  }
  entities.forEach((file) => {
    const modifiedDate = new Date(file.accessed)
    const yearDiff = today.getFullYear() - modifiedDate.getFullYear()
    const monthDiff = today.getMonth() - modifiedDate.getMonth() + yearDiff * 12 // Adjust for year difference
    const dayDiff = Math.floor((today - modifiedDate) / (1000 * 60 * 60 * 24))
    if (dayDiff === 0) {
      grouped["Today"].push(file)
    } else if (dayDiff <= 7) {
      grouped["Earlier this week"].push(file)
    } else if (monthDiff === 0) {
      grouped["Earlier this month"].push(file)
    } else if (yearDiff === 0) {
      grouped["Earlier this year"].push(file)
    } else {
      grouped["Older than a year"].push(file)
    }
  })
  return grouped
}
</script>
