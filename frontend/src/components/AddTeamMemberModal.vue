<template>
  <Dialog
    v-model="showModal"
    :options="{
      title: 'Thành viên',
      size: 'xl',
    }"
  >
    <template #body-content>
      <div class="space-y-6">
        <!-- Current Members List -->
        <div>
          <div class="space-y-3 max-h-60 overflow-y-auto">
            <div
              v-for="member in currentMembers.data || []"
              :key="member.name"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center space-x-3">
                <img
                  v-if="member.user_image"
                  :src="member.user_image"
                  :alt="member.full_name"
                  class="w-10 h-10 rounded-full object-cover"
                />
                <div
                  v-else
                  class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-sm"
                >
                  {{ getInitials(member.full_name) }}
                </div>
                <div>
                  <p class="font-medium text-gray-900">{{ member.full_name }}</p>
                  <p class="text-sm text-gray-500">{{ member.email }}</p>
                </div>
              </div>
              
              <div class="flex items-center space-x-2">
                <select
                  :value="member.access_level"
                  @change="(e) => updateMemberAccess(member.email, parseInt(e.target.value))"
                  :disabled="member.access_level === 2"
                  class="text-sm px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="1">User</option>
                  <option value="2">Manager</option>
                </select>
                
                <Button
                  v-if="member.access_level !== 2"
                  variant="ghost"
                  size="sm"
                  @click="removeMember(member.email)"
                  :loading="removeMemberResource.loading"
                >
                  <LucideX class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- Add Member Section -->
        <div class="border-t pt-6">
          <div class="flex items-center space-x-2 mb-4">
            <LucideUserPlus class="h-5 w-5 text-gray-500" />
            <h3 class="text-lg font-medium text-gray-900">Thêm thành viên</h3>
          </div>

          <div class="space-y-4">
            <!-- Search Input -->
            <div class="relative" ref="searchContainer">
              <FormControl
                v-model="searchQuery"
                type="text"
                placeholder="Tìm kiếm người dùng để thêm..."
                @input="searchUsers"
                @focus="showAllUsers"
                @click="showAllUsers"
                @blur="handleInputBlur"
              >
                <template #prefix>
                  <LucideSearch class="h-4 w-4 text-gray-400" />
                </template>
              </FormControl>

              <!-- User Dropdown -->
              <div
                v-if="showUserDropdown"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
              >
                <div v-if="filteredUsers.length === 0" class="p-3 text-center text-gray-500 text-sm">
                  {{ searchQuery ? 'Không tìm thấy người dùng' : 'Không có người dùng để thêm' }}
                </div>
                <div
                  v-for="user in filteredUsers"
                  :key="user.email"
                  @mousedown.prevent="toggleUserSelection(user)"
                  class="flex items-center space-x-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                  :class="{ 'bg-blue-50': isUserSelected(user) }"
                >
                  <!-- Checkbox -->
                  <input
                    type="checkbox"
                    :checked="isUserSelected(user)"
                    @mousedown.prevent.stop="toggleUserSelection(user)"
                    class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                  
                  <img
                    v-if="user.user_image"
                    :src="user.user_image"
                    :alt="user.full_name"
                    class="w-8 h-8 rounded-full object-cover"
                  />
                  <div
                    v-else
                    class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-xs"
                  >
                    {{ getInitials(user.full_name) }}
                  </div>
                  <div>
                    <p class="font-medium text-gray-900">{{ user.full_name }}</p>
                    <p class="text-sm text-gray-500">{{ user.email }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Selected Users Display -->
            <div v-if="selectedUsers.length > 0" class="mt-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Đã chọn ({{ selectedUsers.length }})
              </label>
              <div class="space-y-2 max-h-48 overflow-y-auto">
                <div
                  v-for="user in selectedUsers"
                  :key="user.email"
                  class="flex items-center justify-between p-3 bg-blue-50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <img
                      v-if="user.user_image"
                      :src="user.user_image"
                      :alt="user.full_name"
                      class="w-8 h-8 rounded-full object-cover"
                    />
                    <div
                      v-else
                      class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-xs"
                    >
                      {{ getInitials(user.full_name) }}
                    </div>
                    <div class="flex-1">
                      <p class="font-medium text-gray-900">{{ user.full_name }}</p>
                      <p class="text-sm text-gray-500">{{ user.email }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-center space-x-2">
                    <select
                      v-model="user.access_level"
                      class="text-sm px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="1">User</option>
                      <option value="2">Manager</option>
                    </select>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      @click="removeUserSelection(user)"
                      class="p-1"
                    >
                      <LucideX class="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Add Button -->
            <Button
              variant="solid"
              @click="addSelectedUsers"
              :loading="addMemberResource.loading"
              :disabled="selectedUsers.length === 0"
              class="w-full"
            >
              Thêm {{ selectedUsers.length > 0 ? selectedUsers.length : '' }} thành viên
            </Button>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <Button
        variant="ghost"
        @click="closeModal"
      >
        Đóng
      </Button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { createResource, Dialog, Button, FormControl } from "frappe-ui"
import { useRoute } from "vue-router"
import { toast } from "@/utils/toasts"
import LucideUserPlus from "~icons/lucide/user-plus"
import LucideSearch from "~icons/lucide/search"
import LucideX from "~icons/lucide/x"

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'success'])

const route = useRoute()
const showModal = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// State
const searchQuery = ref("")
const selectedUsers = ref([])
const showUserDropdown = ref(false)
const searchContainer = ref(null)

// Resources
const allSiteUsers = createResource({
  url: "drive.api.product.get_all_site_users",
  auto: true,
})

const currentMembers = createResource({
  url: "drive.api.product.get_all_users",
  params: {
    team: route.params.team,
  },
  auto: true,
})

const addMemberResource = createResource({
  url: "drive.api.product.add_user_directly_to_team",
  onSuccess: () => {
  },
  onError: (error) => {
    toast(`Lỗi: ${error.message}`)
  },
})

const removeMemberResource = createResource({
  url: "drive.api.product.remove_user",
  onSuccess: () => {
    toast("Thành viên đã được xóa!")
    currentMembers.reload()
    allSiteUsers.reload()
  },
})

const updateAccessResource = createResource({
  url: "drive.api.product.set_user_access",
  onSuccess: () => {
    toast("Quyền truy cập đã được cập nhật!")
    currentMembers.reload()
  },
})

// Computed
const availableUsers = computed(() => {
  if (!allSiteUsers.data || !currentMembers.data) return []
  
  const memberEmails = currentMembers.data.map(member => member.email)
  return allSiteUsers.data.filter(user => !memberEmails.includes(user.email))
})

const filteredUsers = computed(() => {
  if (!availableUsers.value) return []
  
  const selectedEmails = selectedUsers.value.map(u => u.email)
  let users = availableUsers.value.filter(user => !selectedEmails.includes(user.email))
  
  // If there's a search query, filter by it
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    users = users.filter(user => 
      user.full_name.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
    )
  }
  
  return users.slice(0, 10)
})

const accessLevelOptions = [
  { label: "User", value: 1 },
  { label: "Manager", value: 2 },
]

// Methods
const showAllUsers = () => {
  showUserDropdown.value = true
}

const searchUsers = () => {
  // Keep dropdown open when typing
  showUserDropdown.value = true
}

const handleInputBlur = () => {
  // Use setTimeout to allow click events on dropdown items to fire first
  setTimeout(() => {
    showUserDropdown.value = false
  }, 150)
}

const getInitials = (fullName) => {
  if (!fullName) return "U"
  return fullName
    .split(" ")
    .map(name => name.charAt(0))
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

const getAccessLevelText = (level) => {
  switch (level) {
    case 1:
      return "User"
    case 2:
      return "Manager"
    default:
      return "User"
  }
}

const isUserSelected = (user) => {
  return selectedUsers.value.some(u => u.email === user.email)
}

const toggleUserSelection = (user) => {
  const index = selectedUsers.value.findIndex(u => u.email === user.email)
  if (index > -1) {
    selectedUsers.value.splice(index, 1)
  } else {
    // Add default access level when selecting user
    const userWithAccess = { ...user, access_level: 1 }
    selectedUsers.value.push(userWithAccess)
  }
}

const removeUserSelection = (user) => {
  const index = selectedUsers.value.findIndex(u => u.email === user.email)
  if (index > -1) {
    selectedUsers.value.splice(index, 1)
  }
}

const addSelectedUsers = async () => {
  if (selectedUsers.value.length === 0) return
  
  let successCount = 0
  let errorCount = 0
  
  for (const user of selectedUsers.value) {
    try {
      await addMemberResource.submit({
        team: route.params.team,
        email: user.email,
        access_level: user.access_level, // Use individual access level
      })
      successCount++
    } catch (error) {
      errorCount++
      console.error(`Failed to add ${user.email}:`, error)
    }
  }
  
  // Show final result
  if (successCount > 0) {
    toast(`Đã thêm thành công ${successCount} thành viên!`)
    currentMembers.reload()
    allSiteUsers.reload()
    emit('success')
  }
  
  if (errorCount > 0) {
    toast(`Có ${errorCount} thành viên không thể thêm`)
  }
  
  // Reset form
  resetForm()
}

const removeMember = (email) => {
  removeMemberResource.submit({
    team: route.params.team,
    user_id: email,
  })
}

const updateMemberAccess = (email, accessLevel) => {
  updateAccessResource.submit({
    team: route.params.team,
    user_id: email,
    access_level: accessLevel,
  })
}

const resetForm = () => {
  searchQuery.value = ""
  selectedUsers.value = []
  showUserDropdown.value = false
}

const closeModal = () => {
  resetForm()
  showModal.value = false
}

// Click outside to close dropdown
const handleClickOutside = (event) => {
  // Check if click is outside the search container
  if (searchContainer.value && !searchContainer.value.contains(event.target)) {
    showUserDropdown.value = false
  }
}

onMounted(() => {
  // Add a slight delay to ensure the DOM is ready
  setTimeout(() => {
    document.addEventListener('click', handleClickOutside)
  }, 100)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    currentMembers.reload()
    allSiteUsers.reload()
  }
})
</script>
