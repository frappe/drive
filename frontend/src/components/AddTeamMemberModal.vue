<template>
  <Dialog
    v-model="showModal"
    :options="{
      title: 'Thành viên',
      // size: 'xl',
    }"
    class="[&_.dialog-content]:mb-4"
  >
    <template #body-content>
      <div class="space-y-3">
        <!-- Current Members List -->
        <div>
          <div class="space-y-1 max-h-80 overflow-y-auto">
            <div
              v-for="member in currentMembers.data || []"
              :key="member.name"
              class="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center space-x-3">
                <img
                  v-if="member.user_image"
                  :src="member.user_image"
                  :alt="member.full_name"
                  class="w-6 h-6 rounded-full object-cover"
                />
                <div
                  v-else
                  class="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium !text-[10px]"
                >
                  {{ getInitials(member.full_name) }}
                </div>
                <div>
                  <p class="font-medium text-gray-900 text-[14px]">
                    {{ member.full_name }}
                  </p>
                  <!-- <p class="text-sm text-gray-500">{{ member.email }}</p> -->
                </div>
              </div>

              <div class="flex items-center space-x-2">
                <!-- Custom Role Selector -->
                <div class="relative inline-block role-dropdown">
                  <button
                    :disabled="member.access_level === 2"
                    @click="toggleRoleDropdown(member.name)"
                    class="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-full border transition-all duration-200"
                    :class="[
                      member.access_level === 2
                        ? 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-800 border-yellow-200 cursor-not-allowed'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:shadow-sm cursor-pointer',
                      openRoleDropdown === member.name
                        ? 'ring-2 ring-blue-500 ring-opacity-50'
                        : '',
                    ]"
                  >
                    <LucideCrown
                      v-if="member.access_level === 2"
                      class="h-3 w-3 text-yellow-600"
                    />
                    <LucideUser
                      v-else
                      class="h-3 w-3 text-gray-500"
                    />
                    <span>{{
                      member.access_level === 2 ? "Quản lý" : "Thành viên"
                    }}</span>
                    <LucideChevronDown
                      v-if="member.access_level !== 2"
                      class="h-3 w-3 text-gray-400 transition-transform duration-200"
                      :class="{
                        'rotate-180': openRoleDropdown === member.name,
                      }"
                    />
                  </button>

                  <!-- Dropdown Menu -->
                  <div
                    v-if="
                      openRoleDropdown === member.name &&
                      member.access_level !== 2
                    "
                    class="absolute top-full left-0 mt-1 w-36 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1"
                  >
                    <button
                      @click="updateMemberAccess(member.email, 1); closeRoleDropdown()"
                      class="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 flex items-center space-x-2 transition-colors duration-150"
                      :class="{
                        'bg-blue-50 text-blue-700': member.access_level === 1,
                      }"
                    >
                      <LucideUser class="h-3 w-3" />
                      <span>Thành viên</span>
                    </button>
                    <button
                      @click="updateMemberAccess(member.email, 2); closeRoleDropdown()"
                      class="w-full text-left px-3 py-2 text-sm hover:bg-amber-50 flex items-center space-x-2 transition-colors duration-150"
                      :class="{
                        'bg-amber-50 text-amber-700': member.access_level === 2,
                      }"
                    >
                      <LucideCrown class="h-3 w-3" />
                      <span>Quản lý</span>
                    </button>
                  </div>
                </div>

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
        <div class="border-t pt-3">
          <div class="flex flex-row items-center space-x-2 mb-4">
            <LucideUserPlus class="h-5 w-5 text-gray-500" />
            <h3 class="text-lg font-medium text-gray-900">Thêm thành viên</h3>
          </div>

          <div class="space-y-4 relative">
            <!-- Search Input with Pills Inside -->
            <div
              class=""
              ref="searchContainer"
            >
              <div class="relative">
                <!-- Custom Search Input with Pills -->
                <div
                  class="flex items-center flex-wrap gap-1 p-2 border border-gray-300 rounded-lg bg-white min-h-[2.5rem] transition-all duration-200"
                  :class="{
                    'border-blue-500 ring-2 ring-blue-500 ring-opacity-20':
                      showUserDropdown,
                    'border-gray-300': !showUserDropdown,
                  }"
                >
                  <!-- Search Icon -->
                  <LucideSearch class="h-4 w-4 text-gray-400 flex-shrink-0" />

                  <!-- Pills for first 5 selected users -->
                  <div
                    v-for="user in selectedUsers.slice(0, 5)"
                    :key="user.email"
                    class="flex items-center space-x-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm flex-shrink-0"
                  >
                    <img
                      v-if="user.user_image"
                      :src="user.user_image"
                      :alt="user.full_name"
                      class="w-4 h-4 rounded-full object-cover"
                    />
                    <div
                      v-else
                      class="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-[8px]"
                    >
                      {{ getInitials(user.full_name) }}
                    </div>
                    <span class="text-xs font-medium">{{
                      user.full_name
                    }}</span>
                    <button
                      @click="removeUserSelection(user)"
                      class="ml-1 p-0.5 hover:bg-blue-200 rounded-full transition-colors"
                    >
                      <LucideX class="h-3 w-3" />
                    </button>
                  </div>

                  <!-- +N pill for remaining users -->
                  <div
                    v-if="selectedUsers.length > 5"
                    @click="showAllSelectedUsers = !showAllSelectedUsers"
                    class="flex items-center space-x-1 bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-sm cursor-pointer hover:bg-gray-200 transition-colors flex-shrink-0"
                  >
                    <span class="text-xs font-medium"
                      >+{{ selectedUsers.length - 5 }}</span
                    >
                  </div>

                  <!-- Actual Input -->
                  <input
                    v-model="searchQuery"
                    type="text"
                    :placeholder="
                      selectedUsers.length > 0
                        ? 'Tìm thêm...'
                        : 'Tìm kiếm người dùng để thêm...'
                    "
                    @input="searchUsers"
                    @focus="showAllUsers"
                    @click="showAllUsers"
                    @blur="handleInputBlur"
                    class="flex-1 min-w-0 outline-none border-none focus:border-none focus:outline-none focus:ring-0 text-sm placeholder-gray-400 bg-transparent"
                    style="
                      border: none !important;
                      outline: none !important;
                      box-shadow: none !important;
                    "
                  />
                </div>
              </div>

              <!-- User Dropdown -->
              <div
                v-if="showUserDropdown"
                class="z-50 w-full mt-1"
                style="z-index: 9999"
              >
                <div
                  class="bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-hidden"
                >
                  <div class="max-h-48 overflow-y-auto">
                    <div
                      v-if="filteredUsers.length === 0"
                      class="p-3 text-center text-gray-500 text-sm"
                    >
                      {{
                        searchQuery
                          ? "Không tìm thấy người dùng"
                          : "Không có người dùng để thêm"
                      }}
                    </div>
                    <div
                      v-for="user in filteredUsers"
                      :key="user.email"
                      @mousedown.prevent="toggleUserSelection(user)"
                      class="flex items-center space-x-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                      :class="{ 'bg-blue-50': isUserSelected(user) }"
                    >
                      <!-- Checkbox -->
                      <!-- <input
                      type="checkbox"
                      :checked="isUserSelected(user)"
                      @mousedown.prevent.stop="toggleUserSelection(user)"
                      class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    /> -->

                      <img
                        v-if="user.user_image"
                        :src="user.user_image"
                        :alt="user.full_name"
                        class="w-6 h-6 rounded-full object-cover"
                      />
                      <div
                        v-else
                        class="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-[10px]"
                      >
                        {{ getInitials(user.full_name) }}
                      </div>
                      <div>
                        <p class="font-medium text-gray-900 text-[14px]">
                          {{ user.full_name }}
                        </p>
                        <!-- <p class="text-sm text-gray-500">{{ user.email }}</p> -->
                      </div>
                    </div>
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
              class="w-full text-white focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors duration-200"
              :class="{
                '!bg-blue-500 hover:bg-blue-600': selectedUsers.length > 0,
                'bg-gray-300': selectedUsers.length === 0
              }"
            >
              Thêm
              {{ selectedUsers.length > 0 ? selectedUsers.length : "" }} thành
              viên
            </Button>
          </div>
        </div>

        <!-- All Selected Users Modal -->
        <div
          v-if="showAllSelectedUsers && selectedUsers.length > 5"
          class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          @click="showAllSelectedUsers = false"
        >
          <div
            @click.stop
            class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-96 overflow-hidden"
          >
            <div class="p-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">
                Tất cả thành viên đã chọn ({{ selectedUsers.length }})
              </h3>
            </div>
            <div class="p-4 max-h-80 overflow-y-auto">
              <div class="space-y-3">
                <div
                  v-for="user in selectedUsers"
                  :key="user.email"
                  class="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <img
                      v-if="user.user_image"
                      :src="user.user_image"
                      :alt="user.full_name"
                      class="w-6 h-6 rounded-full object-cover"
                    />
                    <div
                      v-else
                      class="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-[10px]"
                    >
                      {{ getInitials(user.full_name) }}
                    </div>
                    <div class="flex-1">
                      <p class="font-medium text-gray-900 text-[14px]">
                        {{ user.full_name }}
                      </p>
                    </div>
                  </div>

                  <div class="flex items-center space-x-2">
                    <!-- Role Selector -->
                    <div class="relative inline-block role-dropdown">
                      <button
                        @click="toggleRoleDropdown(`modal-${user.email}`)"
                        class="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-full border transition-all duration-200 bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:shadow-sm cursor-pointer"
                        :class="{
                          'ring-2 ring-blue-500 ring-opacity-50':
                            openRoleDropdown === `modal-${user.email}`,
                        }"
                      >
                        <LucideCrown
                          v-if="user.access_level === 2"
                          class="h-3 w-3 text-yellow-600"
                        />
                        <LucideUser
                          v-else
                          class="h-3 w-3 text-gray-500"
                        />
                        <span>{{
                          user.access_level === 2 ? "Quản lý" : "Thành viên"
                        }}</span>
                        <LucideChevronDown
                          class="h-3 w-3 text-gray-400 transition-transform duration-200"
                          :class="{
                            'rotate-180':
                              openRoleDropdown === `modal-${user.email}`,
                          }"
                        />
                      </button>

                      <!-- Dropdown Menu -->
                      <div
                        v-if="openRoleDropdown === `modal-${user.email}`"
                        class="absolute top-full left-0 mt-1 w-36 bg-white border border-gray-200 rounded-lg shadow-lg z-60 py-1"
                      >
                        <button
                          @click="user.access_level = 1; closeRoleDropdown()"
                          class="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 flex items-center space-x-2 transition-colors duration-150"
                          :class="{
                            'bg-blue-50 text-blue-700': user.access_level === 1,
                          }"
                        >
                          <LucideUser class="h-3 w-3" />
                          <span>Thành viên</span>
                        </button>
                        <button
                          @click="user.access_level = 2; closeRoleDropdown()"
                          class="w-full text-left px-3 py-2 text-sm hover:bg-amber-50 flex items-center space-x-2 transition-colors duration-150"
                          :class="{
                            'bg-amber-50 text-amber-700':
                              user.access_level === 2,
                          }"
                        >
                          <LucideCrown class="h-3 w-3" />
                          <span>Quản lý</span>
                        </button>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      @click="removeUserSelection(user)"
                      class="p-1"
                    >
                      <LucideX class="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
            <!-- <div class="p-4 border-t border-gray-200">
              <Button
                variant="ghost"
                @click="showAllSelectedUsers = false"
                class="w-full"
              >
                Đóng
              </Button>
            </div> -->
          </div>
        </div>
      </div>
    </template>

    <!-- <template #actions>
      <Button
        variant="ghost"
        @click="closeModal"
      >
        Đóng
      </Button>
    </template> -->
  </Dialog>
</template>

<script setup>
import { toast } from "@/utils/toasts"
import { Button, createResource, Dialog } from "frappe-ui"
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { useRoute } from "vue-router"
import LucideChevronDown from "~icons/lucide/chevron-down"
import LucideCrown from "~icons/lucide/crown"
import LucideSearch from "~icons/lucide/search"
import LucideUser from "~icons/lucide/user"
import LucideUserPlus from "~icons/lucide/user-plus"
import LucideX from "~icons/lucide/x"

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["update:modelValue", "success"])

const route = useRoute()
const showModal = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
})

// State
const searchQuery = ref("")
const selectedUsers = ref([])
const showUserDropdown = ref(false)
const searchContainer = ref(null)
const openRoleDropdown = ref(null)
const showAllSelectedUsers = ref(false)

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
  onSuccess: () => {},
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

  const memberEmails = currentMembers.data.map((member) => member.email)
  return allSiteUsers.data.filter((user) => !memberEmails.includes(user.email))
})

const filteredUsers = computed(() => {
  if (!availableUsers.value) return []

  const selectedEmails = selectedUsers.value.map((u) => u.email)
  let users = availableUsers.value.filter(
    (user) => !selectedEmails.includes(user.email)
  )

  // If there's a search query, filter by it
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    users = users.filter(
      (user) =>
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

const toggleRoleDropdown = (memberName) => {
  openRoleDropdown.value =
    openRoleDropdown.value === memberName ? null : memberName
}

const closeRoleDropdown = () => {
  openRoleDropdown.value = null
}

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
    case 1:
      return "User"
    case 2:
      return "Manager"
    default:
      return "User"
  }
}

const isUserSelected = (user) => {
  return selectedUsers.value.some((u) => u.email === user.email)
}

const toggleUserSelection = (user) => {
  const index = selectedUsers.value.findIndex((u) => u.email === user.email)
  if (index > -1) {
    selectedUsers.value.splice(index, 1)
  } else {
    // Add default access level when selecting user
    const userWithAccess = { ...user, access_level: 1 }
    selectedUsers.value.push(userWithAccess)
  }
}

const removeUserSelection = (user) => {
  const index = selectedUsers.value.findIndex((u) => u.email === user.email)
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
    emit("success")
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
  showAllSelectedUsers.value = false
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
  // Close role dropdown when clicking outside
  if (!event.target.closest(".role-dropdown")) {
    openRoleDropdown.value = null
  }
}

onMounted(() => {
  // Add a slight delay to ensure the DOM is ready
  setTimeout(() => {
    document.addEventListener("click", handleClickOutside)
  }, 100)
})

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside)
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      currentMembers.reload()
      allSiteUsers.reload()
    }
  }
)
</script>

<style scoped>
:deep(.dialog-content) {
  margin-bottom: 1rem !important;
}

:deep(.dialog-backdrop) {
  align-items: flex-start !important;
  padding-top: 2rem !important;
  padding-bottom: 1rem !important;
}

/* Hide scrollbar for dropdown */
.scrollbar-hidden {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
}

.scrollbar-hidden::-webkit-scrollbar {
  display: none; /* WebKit browsers */
}
</style>
