<template>
  <GenericPage
    :grouper="groupByTime"
    :get-entities="getRecents"
    :show-sort="false"
    :empty="{
      icon: LucideClock,
      title: 'No recent files',
      description: 'Try opening something to see it here.',
    }"
  />
</template>

<script setup>
import GenericPage from '@/components/GenericPage.vue'
import { getRecents } from '@/resources/files'
import LucideClock from '~icons/lucide/clock'
// Broken - list view

function groupByTime(entities) {
  const today = new Date()
  const grouped = {
    Today: [],
    'Earlier this week': [],
    'Earlier this month': [],
    'Earlier this year': [],
    'Older than a year': [],
  }
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  entities.forEach((file) => {
    const modifiedDate = new Date(file.accessed)
    const startOfModified = new Date(
      modifiedDate.getFullYear(),
      modifiedDate.getMonth(),
      modifiedDate.getDate(),
    )
    const yearDiff = today.getFullYear() - modifiedDate.getFullYear()
    const monthDiff = today.getMonth() - modifiedDate.getMonth() + yearDiff * 12 // Adjust for year difference
    const dayDiff = Math.round((startOfToday - startOfModified) / (1000 * 60 * 60 * 24))
    if (dayDiff === 0) {
      grouped['Today'].push(file)
    } else if (dayDiff <= 7) {
      grouped['Earlier this week'].push(file)
    } else if (monthDiff === 0) {
      grouped['Earlier this month'].push(file)
    } else if (yearDiff === 0) {
      grouped['Earlier this year'].push(file)
    } else {
      grouped['Older than a year'].push(file)
    }
  })
  return grouped
}
</script>
