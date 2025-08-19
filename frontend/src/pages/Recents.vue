<template>
  <GenericPage
    :grouper="groupByTime"
    :get-entities="getRecents"
    :show-sort="false"
    :icon="LucideClock"
    primary-message="Không có tệp gần đây"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getRecents } from "@/resources/files"
import LucideClock from "~icons/lucide/clock"

function groupByTime(entities) {
  const today = new Date()
  const grouped = {
    [__("Today")]: [],
    [__("Earlier this week")]: [],
    [__("Earlier this month")]: [],
    [__("Earlier this year")]: [],
    [__("Older than a year")]: [],
  }
  entities.forEach((file) => {
    const modifiedDate = new Date(file.accessed)
    const yearDiff = today.getFullYear() - modifiedDate.getFullYear()
    const monthDiff = today.getMonth() - modifiedDate.getMonth() + yearDiff * 12 // Adjust for year difference
    const dayDiff = Math.floor((today - modifiedDate) / (1000 * 60 * 60 * 24))
    if (dayDiff === 0) {
      grouped[__("Today")].push(file)
    } else if (dayDiff <= 7) {
      grouped[__("Earlier this week")].push(file)
    } else if (monthDiff === 0) {
      grouped[__("Earlier this month")].push(file)
    } else if (yearDiff === 0) {
      grouped[__("Earlier this year")].push(file)
    } else {
      grouped[__("Older than a year")].push(file)
    }
  })
  return grouped
}
</script>
