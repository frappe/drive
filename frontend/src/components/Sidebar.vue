<template>
  <div
    :class="[
      isExpanded
        ? 'w-[260px] min-w-[260px] opacity-100 translate-x-0'
        : 'w-[60px] min-w-[60px] ',
      '!transition-all rounded-[8px] bg-white relative hidden sm:flex h-screen flex-col justify-start',
    ]"
  >
    <!-- Header Section -->
    <div class="p-4 py-3 flex items-center gap-2">
      <Button
        @click="toggleExpanded"
        class="rounded-[4px] !bg-[#F5F5F5] !border-[#F5F5F5] !p-[2px]"
      >
        <ChevronLeft class="text-[#404040] h-[18px] w-[18px]" />
      </Button>
      <p
        v-if="isExpanded"
        class="theme-text-color text-[16px] font-bold"
      >
        Bộ lọc
      </p>
    </div>

    <!-- Main Navigation -->
    <div
      class="flex-1"
      :class="!isExpanded ? 'flex flex-col items-center p-2' : 'py-3 px-4'"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <!-- Search at the bottom of main nav -->
      <div>
        <div
          @click="() => emitter.emit('showSearchPopup', true)"
          class="flex h-9 w-full items-center text-gray-700 mb-2 cursor-pointer"
        >
          <div
            class="w-full px-3 py-[10px] !text-black rounded-[8px] group hover:!bg-[#d4e1f9] hover:!text-[#0149C1] search-sidebar-item"
          >
            <div class="flex items-center">
              <!-- Icon cố định ở bên trái -->
              <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                <SearchIconDrive
                  class="w-5 h-5 text-gray-600 group-hover:text-[#0149C1] transition-colors"
                />
              </span>
              <!-- Label với transition opacity -->
              <span
                v-if="isExpanded"
                class="ml-3 text-[14px] group-hover:text-[#0149C1] text-[#404040] font-medium sidebar-label transition-opacity duration-200"
              >
                {{ __("Tìm kiếm") }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tài liệu của tôi -->
      <div class="mb-2">
        <div class="flex h-9 w-full items-center text-gray-700">
          <div
            class="w-full px-3 py-[10px] !text-black rounded-[8px] group hover:!bg-[#d4e1f9] hover:!text-[#0149C1] cursor-pointer search-sidebar-item"
            :class="
              isRouteActive(sidebarItems[0].route)
                ? '!bg-[#d4e1f9] !text-[#0149C1]'
                : ''
            "
            @click="$router.push(sidebarItems[0].route)"
          >
            <div class="flex items-center">
              <!-- Icon cố định ở bên trái -->
              <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                <DocIconDrive
                  class="w-5 h-5 transition-colors"
                  :class="
                    isRouteActive(sidebarItems[0].route)
                      ? 'text-[#0149C1] active_icon'
                      : 'text-gray-600 group-hover:text-[#0149C1]'
                  "
                />
              </span>
              <!-- Label với transition opacity -->
              <span
                v-if="isExpanded"
                class="ml-3 text-[14px] font-medium sidebar-label transition-opacity duration-200"
                :class="
                  isRouteActive(sidebarItems[0].route)
                    ? 'text-[#0149C1]'
                    : 'text-[#404040] group-hover:text-[#0149C1]'
                "
              >
                {{ __("Tài liệu của tôi") }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Nhóm Section với Tooltip -->
      <template
        v-for="item in sidebarItems.slice(1)"
        :key="item.label"
      >
        <div
          v-if="item.label === __('Nhóm')"
          class="mb-2 relative"
        >
          <!-- Nhóm Header với nút Toggle và Add -->
          <div class="flex relative h-9 w-full items-center text-gray-700 mb-2">
            <div
              class="w-full px-3 py-[10px] !text-black rounded-[8px] group hover:!bg-[#d4e1f9] hover:!text-[#0149C1] relative"
              :class="isTeamsExpanded ? '!bg-[#d4e1f9] !text-[#0149C1]' : ''"
              @mouseenter="showTooltip = !isExpanded"
              @mouseleave="showTooltip = false"
            >
              <button
                v-if="isExpanded"
                @click="toggleTeamsExpanded"
                class="flex w-full cursor-pointer items-center justify-between !rounded-[8px] !border-none"
              >
                <div class="flex items-center">
                  <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                    <component
                      :is="item.icon"
                      class="size-5 transition-colors"
                      :class="
                        isTeamsExpanded
                          ? 'text-[#0149C1] active_icon'
                          : 'text-gray-600 group-hover:text-[#0149C1]'
                      "
                    />
                  </span>
                  <span
                    v-if="isExpanded"
                    class="ml-3 text-[14px] font-medium sidebar-label"
                    :class="
                      isTeamsExpanded
                        ? 'text-[#0149C1]'
                        : 'text-[#404040] group-hover:text-[#0149C1]'
                    "
                  >
                    {{ item.label }}
                  </span>
                </div>
                <LucideChevronDown
                  class="h-4 w-4 mr-2 transition-transform duration-200"
                  :class="[
                    { 'rotate-180': !isTeamsExpanded },
                    isTeamsExpanded ? 'text-[#0149C1]' : 'text-black',
                  ]"
                />
              </button>
              <div
                v-else
                class="flex items-center flex-1 cursor-pointer sidebar-tooltip-anchor"
                @click="showTooltip = !showTooltip"
              >
                <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                  <component
                    :is="item.icon"
                    class="size-4 text-gray-600 group-hover:text-[#0149C1] transition-colors"
                  />
                </span>
              </div>

              <!-- Buffer area to make tooltip easier to enter -->
              <div
                v-if="showTooltip && !isExpanded"
                class="fixed sidebar-tooltip-buffer"
                :style="tooltipBufferStyle"
                @mouseenter="showTooltip = true"
                @mouseleave="showTooltip = false"
              ></div>
              <!-- Custom Tooltip cho collapsed sidebar -->
            </div>
            <!-- v-if="showTooltip && !isExpanded" showTooltip && !isExpanded-->

            <div
              v-if="showTooltip && !isExpanded"
              class="fixed bg-white border border-gray-200 rounded-lg shadow-lg py-2 min-w-[200px] max-w-[280px] sidebar-tooltip-panel"
              :style="tooltipPanelStyle"
              @mouseenter="showTooltip = true"
              @mouseleave="showTooltip = false"
            >
              <!-- <div class="!bg-white"> -->

                <!-- Tooltip Header -->
                <div class="px-3 py-2 border-b border-gray-100">
                  <h3 class="text-sm font-medium text-gray-900">
                    {{ item.label }}
                  </h3>
                </div>
  
                <!-- Teams List trong Tooltip -->
                <div class="py-1 max-h-60 overflow-y-auto">
                  <div
                    v-for="teamItem in teamList"
                    :key="teamItem.name"
                    @click="selectTeamFromTooltip(teamItem)"
                    class="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer transition-colors duration-150 group"
                    :class="{
                      'bg-blue-50': team === teamItem.name,
                    }"
                  >
                    <span
                      class="text-sm text-gray-700 flex-1 group-hover:text-gray-900 truncate"
                      :class="{
                        'text-blue-600 font-medium': team === teamItem.name,
                      }"
                    >
                      {{ teamItem.title }}
                    </span>
                    <button
                      v-if="canEditTeam(teamItem)"
                      class="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-100 rounded-full transition-all duration-150"
                      title="Chỉnh sửa tên nhóm"
                      @click.stop="openRenameTeamDialog(teamItem)"
                    >
                      <Pencil
                        class="h-3 w-3 text-gray-400 hover:text-gray-600"
                      />
                    </button>
                  </div>
  
                  <!-- Tạo nhóm mới trong tooltip -->
                  <div class="border-t border-gray-100 mt-1 pt-1">
                    <button
                      @click="createNewTeamFromTooltip"
                      class="flex items-center px-3 py-2 text-sm text-[#0149C1] hover:bg-blue-50 transition-colors duration-150 w-full text-left"
                    >
                      <AddCircleDrive class="mr-2" />
                      Tạo nhóm mới
                    </button>
                  </div>
                </div>
  
                <!-- Tooltip Arrow -->
                <div
                  class="absolute right-full top-3 border-4 border-transparent border-r-white"
                ></div>
                <div
                  class="absolute right-full top-3 mr-px border-4 border-transparent border-r-gray-200"
                ></div>
              <!-- </div> -->
            </div>
          </div>

          <!-- Teams List - Collapsible with animation (chỉ hiện khi expanded) -->
          <Transition name="slide-down">
            <div
              v-if="isExpanded && isTeamsExpanded"
              class="space-y-0.5 border border-[#E5E5E5] rounded-[8px] p-1"
            >
              <!-- Teams List -->
              <div
                v-for="teamItem in teamList"
                :key="teamItem.name"
                @click="selectTeam(teamItem)"
                class="flex items-center p-2 rounded-[8px] hover:bg-[#d4e1f9] hover:!text-[#171717] cursor-pointer transition-colors duration-150 group relative"
                :class="{
                  'bg-[#d4e1f9] !text-[#171717]': team === teamItem.name,
                }"
              >
                <span
                  v-if="isExpanded"
                  class="text-[14px] text-[#171717] flex-1 group-hover:text-[#171717] leading-[20px] font-medium truncate sidebar-label"
                  :class="{ '!text-[#171717]': team === teamItem.name }"
                >
                  {{ teamItem.title }}
                </span>
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

              <button
                v-if="isExpanded"
                @click="createNewTeam"
                class="flex flex-row items-center p-2 gap-2 justify-start text-[#0149C1] text-[14px] leading-[20px] font-medium hover:bg-[#f0f7ff] rounded-[8px] transition-colors duration-150 w-full"
                :title="__('Tạo nhóm mới')"
              >
                <AddCircleDrive />
                <p>Tạo nhóm mới</p>
              </button>
            </div>
          </Transition>
        </div>

        <!-- Other Navigation Items -->
        <div
          v-else-if="item.label !== __('Nhóm')"
          class="mb-2"
        >
          <div class="flex h-9 w-full items-center text-gray-700">
            <div
              class="w-full px-3 py-[10px] !text-black rounded-[8px] group hover:!bg-[#d4e1f9] hover:!text-[#0149C1] cursor-pointer"
              :class="
                isRouteActive(item.route) ? '!bg-[#d4e1f9] !text-[#0149C1]' : ''
              "
              @click="$router.push(item.route)"
            >
              <div class="flex items-center">
                <!-- Icon cố định ở bên trái -->
                <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
                  <component
                    :is="item.icon"
                    class="w-5 h-5 transition-colors"
                    :class="
                      isRouteActive(item.route)
                        ? 'text-[#0149C1] active_icon'
                        : 'text-gray-600 group-hover:text-[#0149C1]'
                    "
                  />
                </span>
                <!-- Label với transition opacity -->
                <span
                  v-if="isExpanded"
                  class="ml-3 text-[14px] font-medium sidebar-label transition-opacity duration-200"
                  :class="
                    isRouteActive(item.route)
                      ? 'text-[#0149C1]'
                      : 'text-[#404040] group-hover:text-[#0149C1]'
                  "
                >
                  {{ item.label }}
                </span>
              </div>
            </div>
          </div>
        </div>
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
      <ButtonFrappe
        variant="ghost"
        @click="showCreateTeamModal = false"
        :disabled="createTeam.loading"
        class="mr-3"
      >
        Hủy
      </ButtonFrappe>
      <ButtonFrappe
        variant="solid"
        @click="handleCreateTeam"
        :loading="createTeam.loading"
        class="!bg-[#0149C1] text-white hover:!opacity-90"
      >
        Tạo nhóm
      </ButtonFrappe>
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
        <ButtonFrappe
          variant="ghost"
          @click="showRenameTeamModal = false"
          :disabled="renameTeam.loading"
          class="mr-3 border border-gray-300 rounded-md"
        >
          Hủy
        </ButtonFrappe>
        <ButtonFrappe
          variant="solid"
          @click="handleRenameTeam"
          :loading="renameTeam.loading"
          class="!bg-[#0149C1] text-white hover:!opacity-90"
        >
          Đổi tên
        </ButtonFrappe>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import AddCircleDrive from "@/assets/Icons/AddCircleDrive.vue"
import DocIconDrive from "@/assets/Icons/DocIconDrive.vue"
import RecentDrive from "@/assets/Icons/RecentDrive.vue"
import SearchIconDrive from "@/assets/Icons/SearchIconDrive.vue"
import ShareDrive from "@/assets/Icons/ShareDrive.vue"
import StarDrive from "@/assets/Icons/StarDrive.vue"
import TeamDrive from "@/assets/Icons/TeamDrive.vue"
import TrashDrive from "@/assets/Icons/TrashDrive.vue"
import SidebarItem from "@/components/SidebarItem.vue"
import { getTeams } from "@/resources/files"
import { notifCount } from "@/resources/permissions"
import { toast } from "@/utils/toasts"
import {
  Dialog,
  FormControl,
  createResource,
  Button as ButtonFrappe,
} from "frappe-ui"
import { ChevronLeft, Pencil } from "lucide-vue-next"
import { Button } from "primevue"
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideFolder from "~icons/lucide/folder"

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

// Tooltip state
const showTooltip = ref(false)

// Rename team state
const showRenameTeamModal = ref(false)
const renameTeamName = ref("")
let renameTargetTeam = null

// Helper function to check if route is active
const isRouteActive = (itemRoute) => {
  const currentPath = route.path

  // Handle exact matches for special routes
  if (itemRoute === "/shared/" && currentPath === "/shared/") {
    return true
  }

  // Handle team routes
  if (itemRoute.includes("/t/")) {
    // Extract the route pattern (e.g., '/recents', '/favourites', '/trash')
    const routePattern = itemRoute.split("/").pop()
    const currentPattern = currentPath.split("/").pop()

    // For root team route (empty pattern)
    if (routePattern === "" || !routePattern) {
      return (
        currentPath === itemRoute ||
        (currentPath.endsWith("/") &&
          currentPath.slice(0, -1) === itemRoute.slice(0, -1))
      )
    }

    // For specific patterns
    return routePattern === currentPattern
  }

  return currentPath === itemRoute
}

const tooltipBufferStyle = ref('')
const tooltipPanelStyle = ref('')

function updateTooltipPosition() {
  nextTick(() => {
    const anchor = document.querySelector('.sidebar-tooltip-anchor')
    if (!anchor) return
    const rect = anchor.getBoundingClientRect()
    tooltipBufferStyle.value = `top: ${rect.top}px; left: ${rect.right + 4}px; width: 18px; height: 100px; z-index:2147483647;`
    tooltipPanelStyle.value = `top: ${rect.top}px; left: ${rect.right + 22}px; min-width:200px; max-width:280px; z-index:2147483647;`
  })
}

watch(() => showTooltip.value, (val) => {
  if (val) updateTooltipPosition()
})
onMounted(() => {
  window.addEventListener('scroll', updateTooltipPosition, true)
  window.addEventListener('resize', updateTooltipPosition)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateTooltipPosition, true)
  window.removeEventListener('resize', updateTooltipPosition)
})

const selectTeamFromTooltip = (team) => {
  showTooltip.value = false
  selectTeam(team)
}

const createNewTeamFromTooltip = () => {
  showTooltip.value = false
  createNewTeam()
}

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
    new_name: renameTeamName.value.trim(),
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
    const errorMessage =
      error.messages?.[0] || "Không thể đổi tên nhóm. Vui lòng thử lại."
    toast(errorMessage)
  },
})

const isExpanded = computed(() => store.state.IsSidebarExpanded)
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

// Watch for sidebar collapse and auto-collapse teams
watch(isExpanded, (newValue, oldValue) => {
  // If sidebar is collapsing (from true to false), close teams section
  if (oldValue === true && newValue === false) {
    isTeamsExpanded.value = false
  }
  // Optional: If sidebar is expanding and teams was collapsed, you might want to expand it
  // else if (oldValue === false && newValue === true) {
  //   isTeamsExpanded.value = true
  // }
})

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
      icon: TeamDrive,
    },
    {
      label: __("Gần đây"),
      route: `/t/${team.value}/recents`,
      icon: RecentDrive,
    },
    {
      label: __("Yêu thích"),
      route: `/t/${team.value}/favourites`,
      icon: StarDrive,
    },
    {
      label: __("Chia sẻ"),
      route: `/shared/`,
      icon: ShareDrive,
    },
    {
      label: __("Thùng rác"),
      route: `/t/${team.value}/trash`,
      icon: TrashDrive,
    },
  ]
  if (getTeams.data && getTeams.data[team.value]?.title === "Your Drive")
    items.splice(1, 1)
  return items
})

const toggleExpanded = () => {
  // If we're collapsing the sidebar, first collapse teams
  if (isExpanded.value) {
    isTeamsExpanded.value = false
    // Small delay to allow teams to collapse first
    setTimeout(() => {
      store.commit("setIsSidebarExpanded", false)
    }, 150)
  } else {
    // If we're expanding the sidebar, expand it immediately
    store.commit("setIsSidebarExpanded", true)
    // Optionally auto-expand teams after sidebar is expanded
    setTimeout(() => {
      isTeamsExpanded.value = true
    }, 200)
  }
}

// Team permission check function
// Check if user is owner
const settings = createResource({
  url: "/api/method/drive.api.product.get_settings",
  method: "GET",
  cache: "settings",
})

function canEditTeam(teamItem) {
  const currentUserId = store.state.user.id

  if (teamItem.name === settings.data?.default_team) {
    return false
  }
  // Check if user is admin in members list
  if (teamItem.users && Array.isArray(teamItem.users)) {
    const userMember = teamItem.users.find(
      (member) =>
        member.user === currentUserId || member.user_id === currentUserId
    )
    console.log(userMember)
    if (userMember) {
      // Check access level (2 = admin)
      if (userMember.access_level === 2) {
        return true
      }
    }
  }

  // Check direct user role
  if (teamItem.user_role === "admin" || teamItem.user_role === "owner") {
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
    teamList.value.forEach((team) => {
      permissions[team.name] = canEditTeam(team)
    })
  }
  return permissions
})

const onEnter = (el) => {
  el.style.height = "0px"
  el.style.opacity = "0"
  el.offsetHeight // trigger reflow

  // Animate to full height
  el.style.transition = "height 0.3s ease-out, opacity 0.3s ease-out"
  el.style.height = el.scrollHeight + "px"
  el.style.opacity = "1"
}

const onLeave = (el) => {
  el.style.height = el.offsetHeight + "px"
  el.offsetHeight // trigger reflow

  el.style.transition = "height 0.3s ease-in, opacity 0.3s ease-in"
  el.style.height = "0px"
  el.style.opacity = "0"
}
</script>

<style scoped>
/* Smooth transitions for sidebar expansion and sliding */
.sidebar-transition {
  transition-property: width, opacity, transform;
  transition-duration: 400ms;
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

/* Icon cố định - không di chuyển */
.sidebar-label {
  transition: opacity 200ms ease-in-out;
}

/* Đảm bảo icon luôn ở vị trí cố định */
.grid.place-items-center {
  position: relative;
  left: 0;
  transition: none; /* Loại bỏ transition cho icon */
}

/* Chỉ text label có transition */
.sidebar-label[v-cloak],
.sidebar-label[style*="display: none"] {
  opacity: 0;
}

.slide-down-enter-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
}

.slide-down-leave-active {
  transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
}

.slide-down-enter-from {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
  padding-top: 0;
  padding-bottom: 0;
}

.slide-down-enter-to {
  max-height: 400px;
  opacity: 1;
  transform: translateY(0);
}

.slide-down-leave-from {
  max-height: 400px;
  opacity: 1;
  transform: translateY(0);
}

.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
  padding-top: 0;
  padding-bottom: 0;
}

/* Target SVG path trực tiếp */
.search-sidebar-item:hover :deep(svg path) {
  stroke: #0149c1 !important;
}

/* Hoặc sử dụng CSS variables */
.search-sidebar-item {
  --icon-color: #404040; /* gray-600 */
}

.search-sidebar-item:hover {
  --icon-color: #0149c1;
}

.active_icon {
  --icon-color: #0149c1 !important;
  stroke: #0149c1 !important;
}

.search-sidebar-item :deep(svg path) {
  stroke: var(--icon-color) !important;
}

.tooltip-arrow {
  position: absolute;
  right: 100%;
  top: 12px;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 6px 6px 6px 0;
  border-color: transparent white transparent transparent;
}

.tooltip-arrow::before {
  content: "";
  position: absolute;
  right: -7px;
  top: -6px;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 6px 6px 6px 0;
  border-color: transparent #e5e7eb transparent transparent;
}
/* Buffer area for tooltip hover */
.sidebar-tooltip-buffer {
  height: 100px;
  width: 20px;
  background: transparent;
  position: absolute;
  left: 30px;
  top: 0 !important;
  z-index: 2147483647;
}
.sidebar-tooltip-panel {
  z-index: 2147483647;
}
</style>
