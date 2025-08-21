<template>
  <div
    :class="[
      isExpanded
        ? 'w-[260px] opacity-100 translate-x-0'
        : 'w-[60px] opacity-80',
      '!transition-all border-r border-gray-200 bg-white relative hidden sm:flex h-screen flex-col justify-start',
    ]"
  >
    <!-- Header Section -->
    <div class="p-4 py-[10px] border-b h-[48px] border-gray-200">
      <PrimaryDropDown :is-expanded="isExpanded" />
    </div>

    <!-- Main Navigation -->
    <div
      class="flex-1 py-3 px-2"
      :class="!isExpanded ? 'flex flex-col items-center' : ''"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <!-- Search at the bottom of main nav -->
      <div>
        <SidebarItem
          :label="__('Tìm kiếm')"
          class="mb-1 hover:bg-gray-50 transition-colors"
          :is-collapsed="!isExpanded"
          @click="() => emitter.emit('showSearchPopup', true)"
        >
          <template #icon>
            <LucideSearch class="size-5" />
          </template>
        </SidebarItem>
      </div>
      <!-- Tài liệu của tôi -->
      <SidebarItem
        :icon="LucideFolder"
        pt-4
        border-t
        border-gray-100
        mt-4
        :label="__('Tài liệu của tôi')"
        :to="sidebarItems[0].route"
        :is-collapsed="!isExpanded"
        class="mb-1"
      />
      <!-- Nhóm Section -->
      <template
        v-for="item in sidebarItems.slice(1)"
        :key="item.label"
      >
        <div
          v-if="item.label === __('Nhóm')"
          class="mb-2"
        >
          <!-- Nhóm Header với nút Toggle và Add -->
          <div
            class="flex h-9 w-full items-center rounded-lg text-gray-700 px-3 py-2 mb-1"
          >
            <button
              v-if="isExpanded"
              @click="toggleTeamsExpanded"
              class="flex items-center justify-between flex-1 rounded-md transition-colors duration-150"
            >
              <div class="flex items-center">
                <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                  <component
                    :is="item.icon"
                    class="size-5 text-black"
                  />
                </span>
                <span
                  v-if="isExpanded"
                  class="ml-3 text-[14px] text-black font-medium sidebar-label"
                >
                  {{ item.label }}
                </span>
              </div>
              <LucideChevronDown
                class="h-4 w-4 mr-2 text-black transition-transform duration-200"
                :class="{ 'rotate-180': !isTeamsExpanded }"
              />
            </button>
            <!-- Icon only when collapsed -->
            <div
              v-else
              class="flex items-center flex-1"
            >
              <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                <component
                  :is="item.icon"
                  class="size-4 text-black"
                />
              </span>
            </div>
            <!-- Nút thêm nhóm -->
            <button
              v-if="isExpanded"
              @click="createNewTeam"
              class="flex h-6 w-6 items-center bg-[#0249c1] justify-center rounded-sm hover:bg-[#0249c1] transition-colors duration-150 ml-1"
              :title="__('Tạo nhóm mới')"
            >
              <LucidePlus class="h-3.5 w-3.5 !text-white" />
            </button>
          </div>

          <!-- Teams List - Collapsible with animation -->
          <div
            v-if="isExpanded && isTeamsExpanded"
            class="ml-5 mr-3 space-y-0.5 border-l border-gray-300 pl-2 transition-all duration-200 ease-in-out"
          >
            <!-- Teams List -->
            <div
              v-for="teamItem in teamList"
              :key="teamItem.name"
              @click="selectTeam(teamItem)"
              class="flex items-center px-2 py-1.5 rounded-md hover:bg-[#0149C1] hover:shadow-md hover:text-white cursor-pointer transition-colors duration-150 group relative"
              :class="{
                'bg-[#0149C1] text-white shadow-md border border-blue-700':
                  team === teamItem.name,
              }"
            >
              <span
                v-if="isExpanded"
                class="text-[14px] text-black flex-1 group-hover:text-white leading-[14px] font-medium truncate sidebar-label"
                :class="{ 'text-white': team === teamItem.name }"
                >{{ teamItem.title }}</span
              >
              <button
                v-if="canEditTeam(teamItem)"
                class="p-1 transition-colors duration-150 flex items-center justify-center absolute right-[2px] top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 focus:opacity-100 pointer-events-auto z-10 bg-white border border-gray-200 rounded-full shadow-sm hover:bg-blue-50 hover:border-blue-400"
                title="Chỉnh sửa tên nhóm"
                tabindex="-1"
                :disabled="renameTeam.loading"
                @click.stop="openRenameTeamDialog(teamItem)"
              >
                <Pencil
                  class="h-3 w-3 text-gray-500 group-hover:text-blue-600 transition-colors duration-150"
                />
              </button>
            </div>
          </div>
        </div>

        <!-- Other Navigation Items -->
        <SidebarItem
          v-else-if="item.label !== __('Nhóm')"
          :icon="item.icon"
          :label="item.label"
          :to="item.route"
          :is-collapsed="!isExpanded"
          class="mb-1"
        />
      </template>
    </div>
    <!-- Storage Bar -->
    <div class="mt-auto p-2 border-t border-gray-100">
      <StorageBar :is-expanded="isExpanded" />
    </div>
  </div>
  
  <!-- Enhanced Create Team Modal -->
  <Dialog
    v-model="showCreateTeamModal"
    :options="{
      title: 'Tạo nhóm mới',
      size: '2xl',
    }"
  >
    <template #body-content>
      <div class="space-y-6">
        <div class="text-center">
          <div
            class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100"
          >
            <LucideBuilding2 class="h-6 w-6 text-blue-600" />
          </div>
          <div class="mt-3">
            <h3 class="text-lg font-medium text-gray-900">Tạo nhóm mới</h3>
            <p class="mt-2 text-sm text-black">
              Tạo một nhóm mới để cộng tác và chia sẻ tài liệu với thành viên
              khác.
            </p>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Tên nhóm <span class="text-red-500">*</span>
          </label>
          <FormControl
            v-model="newTeamName"
            type="text"
            placeholder="Nhập tên nhóm..."
            :disabled="createTeam.loading"
            class="w-full"
            @keyup.enter="handleCreateTeam"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="ghost"
        @click="showCreateTeamModal = false"
        :disabled="createTeam.loading"
        class="mr-3"
      >
        Hủy
      </Button>
      <Button
        variant="solid"
        @click="handleCreateTeam"
        :loading="createTeam.loading"
        class="!bg-[#0149C1] text-white hover:!opacity-90"
      >
        Tạo nhóm
      </Button>
    </template>
  </Dialog>

  <!-- Rename Team Dialog -->
  <Dialog
    v-model="showRenameTeamModal"
    :options="{ title: 'Đổi tên nhóm', size: 'md' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Tên nhóm mới <span class="text-red-500">*</span>
          </label>
          <FormControl
            v-model="renameTeamName"
            type="text"
            placeholder="Nhập tên nhóm mới..."
            :disabled="renameTeam.loading"
            class="w-full"
            @keyup.enter="handleRenameTeam"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div className="flex flex-row justify-end">
        <Button
          variant="ghost"
          @click="showRenameTeamModal = false"
          :disabled="renameTeam.loading"
          class="mr-3 border border-gray-300 rounded-md"
        >
          Hủy
        </Button>
        <Button
          variant="solid"
          @click="handleRenameTeam"
          :loading="renameTeam.loading"
          class="!bg-[#0149C1] text-white hover:!opacity-90"
        >
          Đổi tên
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SidebarItem from "@/components/SidebarItem.vue"
import PrimaryDropDown from "./PrimaryDropdown.vue"
import StorageBar from "./StorageBar.vue"

import { getTeams } from "@/resources/files"
import { notifCount } from "@/resources/permissions"
import { Button, Dialog, FormControl, createResource } from "frappe-ui"

import { toast } from "@/utils/toasts"
import { Pencil } from "lucide-vue-next"
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideChevronDown from "~icons/lucide/chevron-down"
import LucideClock from "~icons/lucide/clock"
import LucideFolder from "~icons/lucide/folder"
import LucidePlus from "~icons/lucide/plus"
import LucideSearch from "~icons/lucide/search"
import LucideStar from "~icons/lucide/star"
import LucideTrash from "~icons/lucide/trash"
import LucideUsers from "~icons/lucide/users"

defineEmits(["toggleMobileSidebar", "showSearchPopUp"])
const store = useStore()
const route = useRoute()
const router = useRouter()
notifCount.fetch()

// Create team modal state
const showCreateTeamModal = ref(false)
const newTeamName = ref("")

// Teams collapse state - default is expanded (true)
const isTeamsExpanded = ref(true)

// Rename team state
const showRenameTeamModal = ref(false)
const renameTeamName = ref("")
let renameTargetTeam = null

// Create team resource
const createTeam = createResource({
  url: "drive.api.product.create_personal_team",
  makeParams: () => ({
    team_name: newTeamName.value,
    email: store.state.user.id,
  }),
  onSuccess: (data) => {
    if (data) {
      toast("Nhóm đã được tạo thành công!")
      // Refresh teams data
      getTeams.fetch()
      // Close modal and reset form
      showCreateTeamModal.value = false
      newTeamName.value = ""
      // Navigate to new team's team page using Vue Router
      router.push(`/t/${data}/team`)
    }
  },
  onError: (error) => {
    toast("Không thể tạo nhóm. Vui lòng thử lại.")
    console.error("Create team error:", error)
  },
})

// Rename team resource
const renameTeam = createResource({
  url: "drive.drive.doctype.drive_team.drive_team.change_team_name",
  makeParams: () => ({
    team_id: renameTargetTeam?.name,
    new_name: renameTeamName.value.trim()
  }),
  onSuccess: (data) => {
    toast("Đã đổi tên nhóm thành công!")
    // Refresh teams data
    getTeams.fetch()
    // Close modal and reset form
    showRenameTeamModal.value = false
    renameTeamName.value = ""
    renameTargetTeam = null
  },
  onError: (error) => {
    console.error("Rename team error:", error)
    const errorMessage = error.messages?.[0] || "Không thể đổi tên nhóm. Vui lòng thử lại."
    toast(errorMessage)
  },
})

const isExpanded = computed(() => store.state.IsSidebarExpanded)
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

getTeams.fetch()
const teamList = computed(() => Object.values(getTeams.data || {}))

const selectedTeam = computed({
  get() {
    const currentTeam = teamList.value.find((t) => t.name === team.value)
    return currentTeam ? { label: currentTeam.title } : null
  },
  set(val) {
    const target = teamList.value.find((t) => t.title === val?.label)
    if (target) router.push(`/t/${target.name}/team`)
  },
})

const teamAutocompleteOptions = computed(() =>
  teamList.value.map((t) => ({ label: t.title }))
)

const teamDropdownOptions = computed(() =>
  teamList.value.map((t) => ({
    label: t.title,
    onClick: () => {
      router.push(`/t/${t.name}/team`)
    },
  }))
)

const sidebarItems = computed(() => {
  const items = [
    {
      label: __("Tài liệu của tôi"),
      route: `/t/${team.value}/`,
      icon: LucideFolder,
    },
    {
      label: __("Nhóm"),
      route: `/t/${team.value}/team`,
      icon: LucideBuilding2,
    },
    {
      label: __("Gần đây"),
      route: `/t/${team.value}/recents`,
      icon: LucideClock,
    },
    {
      label: __("Yêu thích"),
      route: `/t/${team.value}/favourites`,
      icon: LucideStar,
    },
    {
      label: __("Chia sẻ"),
      route: `/shared/`,
      icon: LucideUsers,
    },
    {
      label: __("Thùng rác"),
      route: `/t/${team.value}/trash`,
      icon: LucideTrash,
    },
  ]
  if (getTeams.data && getTeams.data[team.value]?.title === "Your Drive")
    items.splice(1, 1)
  return items
})

const toggleExpanded = () =>
  store.commit("setIsSidebarExpanded", isExpanded.value ? false : true)

// Team permission check function
function canEditTeam(teamItem) {
  const currentUserId = store.state.user.id
  console.log(teamItem)
  // Check if user is owner
  if (teamItem.owner === currentUserId) {
    return true
  }
  
  // Check if user is admin in members list
  if (teamItem.members && Array.isArray(teamItem.members)) {
    const userMember = teamItem.members.find(
      member => member.user === currentUserId || member.user_id === currentUserId
    )
    
    if (userMember) {
      // Check admin flag
      if (userMember.is_admin === 1 || userMember.is_admin === true) {
        return true
      }
      
      // Check access level (2 = admin)
      if (userMember.access_level === 2) {
        return true
      }
    }
  }
  
  // Check direct user role
  if (teamItem.user_role === 'admin' || teamItem.user_role === 'owner') {
    return true
  }
  
  // Check if teamItem has can_edit property (from enhanced API)
  if (teamItem.can_edit === true) {
    return true
  }
  
  // Default: no permission
  return false
}

// Team methods
const toggleTeamsExpanded = () => {
  isTeamsExpanded.value = !isTeamsExpanded.value
}

const selectTeam = (team) => {
  router.push(`/t/${team.name}/team`)
}

const createNewTeam = () => {
  showCreateTeamModal.value = true
}

const handleCreateTeam = () => {
  if (!newTeamName.value?.trim()) {
    toast("Vui lòng nhập tên nhóm.")
    return
  }
  createTeam.submit()
}

// Rename team methods
function openRenameTeamDialog(teamItem) {
  // Check permission first
  if (!canEditTeam(teamItem)) {
    toast("Bạn không có quyền đổi tên nhóm này.")
    return
  }
  
  renameTargetTeam = teamItem
  renameTeamName.value = teamItem.title
  showRenameTeamModal.value = true
}

function handleRenameTeam() {
  if (!renameTeamName.value?.trim()) {
    toast("Vui lòng nhập tên nhóm mới.")
    return
  }
  
  if (renameTeamName.value.trim() === renameTargetTeam?.title) {
    toast("Tên mới không được giống tên hiện tại.")
    return
  }
  
  renameTeam.submit()
}

// Alternative: Computed property for caching permissions (optional optimization)
const teamPermissions = computed(() => {
  const permissions = {}
  if (teamList.value) {
    teamList.value.forEach(team => {
      permissions[team.name] = canEditTeam(team)
    })
  }
  return permissions
})
</script>

<style scoped>
/* Smooth transitions for sidebar expansion and sliding */
.sidebar-transition {
  transition-property: width, opacity, transform;
  transition-duration: 350ms;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Teams collapse animation */
.transition-all {
  transition-property: all;
}

/* Chevron rotation animation */
.rotate-180 {
  transform: rotate(180deg);
}

/* Ẩn label khi sidebar thu nhỏ để tránh text bị co lại */
.sidebar-label {
  transition: opacity 0.2s;
}
.sidebar-label[v-cloak],
.sidebar-label[style*="display: none"] {
  opacity: 0;
}
</style>