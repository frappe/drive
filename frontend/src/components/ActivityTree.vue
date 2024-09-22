<template>
  <div
    v-for="(group, i) in groupedActivityLog"
    :key="i"
    class="px-4 pb-2 gap-x-2"
  >
    <span
      v-if="group.length && Object.keys(groupedActivityLog).length > 1"
      class="text-base text-gray-600 font-medium leading-6"
    >
      {{ i }}
    </span>
    <div
      v-for="activity in group"
      :key="activity"
      class="flex flex-col items-start justify-start py-3"
    >
      <div class="text-base flex items-start justify-start gap-x-2">
        <Avatar
          size="lg"
          :image="activity.user_image"
          :label="activity.full_name"
        />
        {{ activity.message }}
      </div>
      <span class="pl-9 text-xs text-gray-600 -mt-1 mb-3">{{
        activity.creation
      }}</span>
      <div
        v-if="activity.document_type === 'Drive Entity'"
        class="flex items-center justify-start ml-8.5 flex-wrap gap-1"
      >
        <template v-if="activity.action_type === 'rename'">
          <ActivityTreeItem
            :entity="entity"
            :activity="activity"
            :title="activity.old_value"
            :strike-through="true"
          />

          <ArrowRight class="text-gray-500 h-4" />
          <ActivityTreeItem
            :activity="activity"
            :entity="entity"
            :title="activity.new_value"
          />
        </template>
        <ActivityTreeItem
          v-else
          :entity="entity"
          :activity="activity"
          :title="activity.new_value"
        />
      </div>
      <div
        v-if="activity.document_type === 'Drive DocShare'"
        class="flex items-center justify-start ml-8.5 flex-wrap gap-1"
      >
        <div
          :title="title ? title : entity.title"
          class="border max-w-[220px] rounded-[7px] px-1 py-1 flex items-center justify-center gap-x-1 overflow-clip"
        >
          <Avatar size="xs" :image="activity.share_user_image" />
          <span
            class="text-sm line-clamp-1"
            :class="strikeThrough ? 'line-through text-gray-600' : ''"
            >{{ activity.share_user_fullname }}</span
          >
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useStore } from "vuex"
import { Avatar, createResource } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { ArrowRight } from "lucide-vue-next"
import { formatDate } from "../utils/format"
import ActivityTreeItem from "./ActivityTreeItem.vue"

const store = useStore()

const entity = computed(() => {
  if (store.state.entityInfo && store.state.entityInfo.length > 1) {
    return store.state.entityInfo.length
  } else if (store.state.entityInfo?.length) {
    return store.state.entityInfo[0]
  } else if (store.state.currentFolder?.length) {
    return store.state.currentFolder[0]
  } else {
    return false
  }
})

// update watcher if this is changed
const groupedActivityLog = ref({
  Today: [],
  Yesterday: [],
  "This week": [],
  "Last week": [],
  "This month": [],
  "Earlier this year": [],
  "Older than a year": [],
})

const showInfoSidebar = computed(() => {
  return store.state.showInfo
})

const entityText = computed(() => {
  if (entity.value.is_group) {
    return "folder"
  }
  if (entity.value.document) {
    return "document"
  }
  return "file"
})

const currentUserEmail = computed(() => {
  return store.state.auth.user_id
})

watch([entity, showInfoSidebar], ([newEntity, newShowInfoSidebar]) => {
  if (
    newEntity &&
    typeof newEntity !== "number" &&
    typeof newEntity !== "undefined"
  ) {
    if (newShowInfoSidebar == true) {
      groupedActivityLog.value = {
        Today: [],
        Yesterday: [],
        "This week": [],
        "Last week": [],
        "This month": [],
        "Earlier this year": [],
        "Older than a year": [],
      }
      activityLog.fetch({ entity_name: newEntity.name })
    }
  }
})

function generateMessage(activity) {
  const user = activity.full_name ? activity.full_name : activity.owner
  const creationText =
    entity.value.is_group || entity.value.document ? "created" : "uploaded"
  if (activity.document_type === "Drive Entity") {
    switch (activity.action_type) {
      case "create":
        return `${user} ${creationText} ${entityText.value}`
      case "rename":
        return `${user} renamed this ${entityText.value}`

      case "update":
        return `${user} edited this ${entityText.value}`

      case "delete":
        return `${user} deleted this ${entityText.value}`

      case "move":
        return `${user} moved this ${entityText.value}`

      default:
        return `Unknown action type: ${activity.action_type}`
    }
  }
  if (activity.document_type === "Drive DocShare") {
    switch (activity.action_type) {
      case "create":
        if (activity.document_type == "Drive DocShare") {
          return `${user} shared this ${entityText.value} with`
        }
        return `${user} edited this ${entityText.value}`
    }
  }
}

function groupAndTransform(activities) {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  const startOfWeek = new Date(today)
  startOfWeek.setDate(today.getDate() - today.getDay())

  activities.forEach((activity) => {
    const creationDate = new Date(activity.creation)
    const dayDiff = Math.floor((today - creationDate) / (1000 * 60 * 60 * 24))
    const yearDiff = today.getFullYear() - creationDate.getFullYear()
    const monthDiff = today.getMonth() - creationDate.getMonth() + yearDiff * 12

    // ttansform
    activity.full_name =
      activity.owner === currentUserEmail.value ? "You" : activity.full_name
    activity.message = generateMessage(activity)
    activity.creation = formatDate(activity.creation)

    // calc and group by creation
    switch (true) {
      case creationDate.toDateString() === today.toDateString():
        groupedActivityLog.value.Today.push(activity)
        break
      case creationDate.toDateString() === yesterday.toDateString():
        groupedActivityLog.value.Yesterday.push(activity)
        break
      case creationDate >= startOfWeek:
        groupedActivityLog.value["This week"].push(activity)
        break
      case dayDiff <= 14 &&
        creationDate >=
          new Date(startOfWeek.getTime() - 7 * 24 * 60 * 60 * 1000):
        groupedActivityLog.value["Last week"].push(activity)
        break
      case monthDiff === 0:
        groupedActivityLog.value["This month"].push(activity)
        break
      case yearDiff === 0:
        groupedActivityLog.value["Earlier this year"].push(activity)
        break
      default:
        groupedActivityLog.value["Older than a year"].push(activity)
    }
  })
}

const activityLog = createResource({
  url: "drive.api.activity.get_entity_activity_log",
  params: { entity_name: entity.value.name },
  onSuccess(data) {
    groupAndTransform(data)
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages)
    }
  },
  reset() {
    groupedActivityLog.value = []
  },
  auto: entity.value,
})
</script>
