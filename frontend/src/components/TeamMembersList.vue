<template>
  <div class="bg-white border-l border-gray-200 w-80 h-full flex flex-col">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200">
      <div class="flex items-start justify-between">
        <div>
          <h3 class="text-sm font-medium text-gray-900">Thành viên</h3>
          <p class="text-xs text-gray-500 mt-1">
            {{ teamMembers.length }} thành viên
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          @click="showAddMemberModal = true"
          class="!bg-blue-500 text-white hover:!bg-blue-600"
        >
          <div class="flex flex-row items-center space-x-2">
            <LucideUserPlus class="h-4 w-4" />
            <span class="text-xs">Thêm thành viên</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Members Grid -->
    <div class="flex-1 overflow-y-auto p-4">
      <div class="grid grid-cols-6 gap-2 mb-4">
        <div
          v-for="member in regularMembers"
          :key="member.name"
          class="flex flex-col items-center"
          :title="member.full_name"
        >
          <img
            v-if="member.user_image"
            :src="member.user_image"
            :alt="member.full_name"
            class="w-8 h-8 rounded-full object-cover"
          />
          <div
            v-else
            class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-xs"
          >
            {{ getInitials(member.full_name) }}
          </div>
        </div>
      </div>

      <!-- Manager Section -->
      <div
        v-if="manager"
        class="mt-6"
      >
        <h4 class="text-xs font-medium text-gray-500 mb-2">Trưởng nhóm</h4>
        <div class="flex items-center space-x-2">
          <img
            v-if="manager.user_image"
            :src="manager.user_image"
            :alt="manager.full_name"
            class="w-8 h-8 rounded-full object-cover"
          />
          <div
            v-else
            class="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white font-medium text-xs"
          >
            {{ getInitials(manager.full_name) }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ manager.full_name }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Member Modal -->
    <AddTeamMemberModal
      v-model="showAddMemberModal"
      @success="getTeamMembers.reload()"
    />
  </div>
</template>

<script setup>
import { Button, createResource } from "frappe-ui"
import { computed, onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import LucideUserPlus from "~icons/lucide/user-plus"
import AddTeamMemberModal from "./AddTeamMemberModal.vue"

const route = useRoute()

// Modal state
const showAddMemberModal = ref(false)

// Get team members
const getTeamMembers = createResource({
  url: "drive.api.product.get_all_users",
  params: {
    team: route.params.team,
  },
  auto: true,
})

const teamMembers = computed(() => getTeamMembers.data || [])

// Separate regular members and manager
const regularMembers = computed(() =>
  teamMembers.value.filter((member) => member.access_level !== 2)
)

const manager = computed(() =>
  teamMembers.value.find((member) => member.access_level === 2)
)

const getInitials = (fullName) => {
  if (!fullName) return "U"
  return fullName
    .split(" ")
    .map((name) => name.charAt(0))
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

const getAccessLevelText = (level) => {
  switch (level) {
    case 0:
      return "Viewer"
    case 1:
      return "Editor"
    case 2:
      return "Manager"
    default:
      return "Member"
  }
}

// Refetch when team changes
onMounted(() => {
  if (route.params.team) {
    getTeamMembers.reload()
  }
})
</script>
