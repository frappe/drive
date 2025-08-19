<template>
  <template
    v-for="(group, i) in groupedActivityLog"
    :key="i"
  >
    <div
      v-if="group.length && Object.keys(groupedActivityLog).length > 1"
      class="px-5 pb-2 gap-x-2"
    >
      <span class="text-base text-ink-gray-5 font-medium leading-6">
        {{ __(i) }}
      </span>
      <div
        v-for="activity in group"
        :key="activity"
        class="flex items-start justify-start py-3 gap-x-2"
      >
        <Avatar
          size="md"
          :image="activity.user_image"
          :label="activity.full_name"
        />
        <div class="flex flex-col items-start justify-center">
          <span class="text-sm text-ink-gray-9">{{
            __(activity.message)
          }}</span>
          <span class="text-xs text-ink-gray-5 mb-3">{{
            activity.creation
          }}</span>

          <template v-if="activity.action_type === 'rename'">
            <div class="flex items-center justify-start flex-wrap gap-1">
              <ActivityTreeItem
                :entity="entity"
                :activity="activity"
                :title="activity.old_value"
                :strike-through="true"
              />

              <ArrowRight class="text-ink-gray-4 h-4" />
              <ActivityTreeItem
                :activity="activity"
                :entity="entity"
                :title="activity.new_value"
              />
            </div>
          </template>
          <ActivityTreeShare
            v-else-if="activity.action_type.startsWith('share')"
            :activity="activity"
          >
            <template
              v-if="activity.nested"
              #nested
            >
              <div
                v-for="nested in activity.nested"
                :key="nested.name"
              >
                <ActivityTreeShare
                  v-if="activity.nested"
                  :activity="nested"
                />
              </div>
            </template>
          </ActivityTreeShare>

          <ActivityTreeItem
            v-else
            :entity="entity"
            :activity="activity"
            :title="activity.new_value"
          />
        </div>
      </div>
    </div>
  </template>
</template>
<script setup>
import { Avatar, createResource } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useStore } from "vuex"
import ArrowRight from "~icons/lucide/arrow-right"
import { formatDate } from "../utils/format"
import ActivityTreeItem from "./ActivityTreeItem.vue"
import ActivityTreeShare from "./ActivityTreeShare.vue"

const store = useStore()
const props = defineProps({ entity: Object })

const entity = computed(() => props.entity)

const activityLog = createResource({
  url: "drive.api.activity.get_entity_activity_log",
  params: { entity_name: entity.value.name },
  onSuccess: groupAndTransform,
})
const groupedActivityLog = ref()
watch(
  entity,
  () => {
    groupedActivityLog.value = {
      [__("Today")]: [],
      [__("Yesterday")]: [],
      [__("This week")]: [],
      [__("Last week")]: [],
      [__("This month")]: [],
      [__("This year")]: [],
      [__("Older than a year")]: [],
    }
    activityLog.fetch({ entity_name: entity.value.name })
  },
  { immediate: true }
)

const entityText = computed(() => {
  if (entity.value.is_group) {
    return __("folder")
  }
  return __("file")
})

function generateMessage(activity) {
  const user = activity.full_name ? activity.full_name : activity.owner
  const creationText =
    entity.value.is_group || entity.value.document
      ? __("created this")
      : __("uploaded this")

  switch (activity.action_type) {
    case "create":
      return `${user} ${creationText} ${entityText.value}`
    case "rename":
      return `${user} ${__("renamed this")} ${entityText.value}`
    case "edit":
      return `${user} ${__("edited this")} ${entityText.value}`
    case "delete":
      return `${user} ${__("deleted this")} ${entityText.value}`
    case "share_add":
      return `${user} ${__("shared this")} ${entityText.value}`
    case "share_edit":
      return `${user} ${__("updated permissions on this")} ${entityText.value}`
    case "share_remove":
      return `${user} ${__("restricted this")} ${entityText.value}`
    case "move":
      return `${user} ${__("moved this")} ${entityText.value}`
    default:
      return `${__("Unknown action type")}: ${activity.action_type}`
  }
}

function groupAndTransform(activities) {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  const startOfWeek = new Date(today)
  startOfWeek.setDate(today.getDate() - today.getDay())
  const timeThreshold = 15 * 60 * 1000
  // Transform and reduce loop
  for (let index = 0; index < activities.length; index++) {
    let activity = activities[index]
    if (index > 0) {
      const prevActivity = activities[index - 1]
      const currentTime = new Date(activity.creation).getTime()
      const prevTime = new Date(prevActivity.creation).getTime()
      if (
        prevActivity.action_type === activity.action_type &&
        prevActivity.owner === activity.owner &&
        prevActivity.document_field === activity.document_field &&
        currentTime - prevTime <= timeThreshold
      ) {
        if (!prevActivity.nested) {
          prevActivity.nested = []
        }
        prevActivity.nested.push(activity)
        activities.splice(index, 1)
        index--
      }
    }
    activity.full_name =
      activity.owner === store.state.user.id ? __("You") : activity.full_name
    activity.message = generateMessage(activity)
    activity.creation = formatDate(activity.creation)
  }
  // calc and group by creation loop
  activities.forEach((activity) => {
    const creationDate = new Date(activity.creation)
    const dayDiff = Math.floor((today - creationDate) / (1000 * 60 * 60 * 24))
    const yearDiff = today.getFullYear() - creationDate.getFullYear()
    const monthDiff = today.getMonth() - creationDate.getMonth() + yearDiff * 12
    switch (true) {
      case creationDate.toDateString() === today.toDateString():
        groupedActivityLog.value[__("Today")].push(activity)
        break
      case creationDate.toDateString() === yesterday.toDateString():
        groupedActivityLog.value[__("Yesterday")].push(activity)
        break
      case creationDate >= startOfWeek:
        groupedActivityLog.value[__("This week")].push(activity)
        break
      case dayDiff <= 14 &&
        creationDate >=
          new Date(startOfWeek.getTime() - 7 * 24 * 60 * 60 * 1000):
        groupedActivityLog.value[__("Last week")].push(activity)
        break
      case monthDiff === 0:
        groupedActivityLog.value[__("This month")].push(activity)
        break
      case yearDiff === 0:
        groupedActivityLog.value[__("This year")].push(activity)
        break
      default:
        groupedActivityLog.value[__("Older than a year")].push(activity)
    }
  })
}
</script>
