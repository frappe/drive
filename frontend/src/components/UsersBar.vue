<template>
  <Popover
    transition="default"
    placement="bottom-end"
    popover-class="border-t-8 border-transparent"
  >
    <template #target="{ togglePopover }">
      <div
        class="ml-2.5 flex items-center rounded-md cursor-pointer"
        @click="togglePopover()"
      >
        <div
          v-for="user in connectedUsers"
          :key="user.name"
          class="-ml-2.5 -py-0.5 flex items-center rounded-full"
        >
          <Avatar
            class="-"
            :size="'md'"
            :style="{
              border: '2px solid',
              borderRadius: '100%',
              borderColor: user.color,
            }"
            :image="user.avatar"
            :label="user.name"
            :title="user.name"
          />
        </div>
      </div>
    </template>
    <template #body-main>
      <div class="px-3 py-1">
        <div
          v-for="user in connectedUsers"
          :key="user.name"
          class="flex justifty items-center gap-2 py-1"
        >
          <Avatar
            :size="'md'"
            :image="user.avatar"
            :label="user.name"
            :title="user.name"
          />
          <span class="text-sm text-ink-gray-8 mr-4">{{ user.name }}</span>
          <svg
            class="ml-auto"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="8"
              cy="8"
              r="4.5"
              fill="transparent"
              :stroke="user.color"
              stroke-width="3"
            />
          </svg>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script>
import { Avatar, Popover } from "frappe-ui"
import { mapState } from "vuex"

export default {
  name: "UsersBar",
  components: {
    Avatar,
    Popover,
  },
  computed: mapState(["connectedUsers"]),
}
</script>
