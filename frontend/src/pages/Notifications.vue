<template>
  <div class="h-full overflow-y-auto mt-3.5 px-4 w-full bg-surface-white">
    <div class="w-full h-7 mb-6 flex items-start justify-between">
      <div
        class="bg-surface-gray-2 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
      >
        <Button
          class="max-h-6"
          :class="
            onlyUnread
              ? 'bg-surface-white shadow-sm hover:bg-surface-white active:bg-surface-white'
              : ''
          "
          @click="onlyUnread = true"
        >
          Unread
        </Button>
        <Button
          class="max-h-6"
          :class="
            onlyUnread
              ? ''
              : 'bg-surface-white shadow-sm hover:bg-surface-white active:bg-surface-white'
          "
          @click="onlyUnread = false"
        >
          All
        </Button>
      </div>
      <div>
        <Button
          :loading="notifications.loading"
          icon="refresh-ccw"
          class="mr-2"
          @click="notifications.reload()"
        />
        <Button
          icon-left="check-circle"
          @click="
            markAsRead.submit({ all: true }), (store.state.notifCount = 0)
          "
        >
          Mark all as Read
        </Button>
      </div>
    </div>

    <ListView
      v-if="!notifications.loading && notifications.data.length"
      :columns="columns"
      :options="options"
      :rows="notifications.data"
      row-key="name"
    />
    <div
      v-else
      class="flex flex-col items-center justify-center m-auto h-full"
      style="transform: translate(0, -42px)"
    >
      <LucideInbox class="w-14 h-auto text-ink-gray-4 pb-4" />
      <span class="text-base text-ink-gray-5 font-medium"
        >No Notifications</span
      >
    </div>
  </div>
</template>
<script setup>
import { ref, h, watch } from "vue"
import { formatTimeAgo } from "@vueuse/core"
import { createResource, Avatar, ListView } from "frappe-ui"
import { useStore } from "vuex"
import { formatDate } from "@/utils/format"
import emitter from "@/emitter"
import { LucideInbox } from "lucide-vue-next"

const store = useStore()
const onlyUnread = ref(true)
const options = {
  getRowRoute: (row) => ({
    name: row.entity_type,
    params: { entityName: row.notif_doctype_name },
  }),
  onRowClick: (row) => {
    if (row.type === "Team") emitter.emit("showSettings", 1)
    if (onlyUnread.value) {
      markAsRead.submit({ name: row.name })
      store.state.notifCount = store.state.notifCount - 1
    }
  },
  selectable: false,
  showTooltip: true,
  resizeColumn: false,
}

const columns = [
  {
    label: "Subject",
    key: "subject",
    width: "80px",
    getLabel: ({ row }) => row.type,
  },
  {
    label: "Message",
    key: "message",
    width: 4,
    getLabel: ({ row }) => row.message,
    prefix: ({ row }) => {
      if (row.from_user)
        return h(Avatar, {
          shape: "circle",
          label: row.from_user,
          image: row.user_image,
          size: "sm",
        })
    },
  },
  {
    key: "creation",
    align: "end",
    getLabel: ({ row }) => row.relativeTime,
  },
]

watch(onlyUnread, (newValue) => {
  notifications.fetch({
    only_unread: newValue,
  })
})

const notifications = createResource({
  url: "drive.api.notifications.get_notifications",
  auto: true,
  params: {
    only_unread: onlyUnread.value,
  },
  onSuccess(data) {
    data.forEach((item) => {
      item.relativeTime = formatTimeAgo(new Date(item.creation))
      item.creation = formatDate(item.creation)
    })
  },
})

const markAsRead = createResource({
  url: "drive.api.notifications.mark_as_read",
  auto: false,
  method: "POST",
  params: {
    name: "",
    all: false,
  },
  onSuccess() {
    notifications.reload()
  },
})
</script>
