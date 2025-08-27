<template>
  <div class="bg-white border-l border-gray-200 w-80 h-full flex flex-col min-w-[320px] py-5 px-4">
    <!-- Header -->
    <div class="flex items-start justify-between flex-wrap gap-4">
      <div>
        <h3 class="text-[16px] font-bold text-gray-900">Thành viên</h3>
        <!-- <p class="text-xs text-gray-500 mt-1">
          {{ teamMembers.length }} thành viên
        </p> -->
      </div>
      <div class="flex flex-row items-center gap-2">
        <LucideCirclePlus 
          @click="showAddMemberModal = true" 
          stroke="#737373" 
          class="h-5 w-5 cursor-pointer hover:stroke-gray-600 transition-colors" 
        />
        <X 
          @click="handleClose" 
          stroke="#737373" 
          class="h-5 w-5 cursor-pointer hover:stroke-gray-600 transition-colors" 
        />
      </div>
    </div>

    <!-- Members Grid -->
    <div class="flex-1 overflow-y-auto mt-[20px]">
      <!-- Manager Section -->
      <div v-if="manager" class="mb-4">
        <h4 class="text-[14px] font-bold text-black mb-2">Trưởng nhóm</h4>
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
      
      <p class="text-[14px] font-bold text-black mb-2">Thành viên khác</p>
      <div class="grid grid-cols-6 gap-2.5 mb-4">
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
import LucideCirclePlus from "~icons/lucide/circle-plus";
import { X } from 'lucide-vue-next';

const route = useRoute()

// Khai báo emits trong Vue 3 Composition API
const emit = defineEmits(['close'])

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

// Handle close event
const handleClose = () => {
  console.log('Closing TeamMembersList...') // Debug log
  emit('close')
}

// Refetch when team changes
onMounted(() => {
  if (route.params.team) {
    getTeamMembers.reload()
  }
})
</script>