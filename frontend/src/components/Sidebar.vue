<template>
  <div
    :class="isExpanded ? 'w-[220px]' : 'w-[50px]'"
    class="border-r bg-surface-menu-bar relative hidden sm:flex h-screen flex-col justify-start duration-300 ease-in-out p-2"
  >
    <PrimaryDropDown :is-expanded="isExpanded" />
    <div
      class="mt-2.5"
      :class="!isExpanded ? 'flex flex-col items-start' : ''"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <SidebarItem
        :label="__('Tìm kiếm')"
        class="mb-1"
        :is-collapsed="!isExpanded"
        @click="() => emitter.emit('showSearchPopup', true)"
      >
        <template #icon>
          <LucideCommand class="size-4" />
        </template>
      </SidebarItem>
      <SidebarItem
        :icon="sidebarItems[0].icon"
        :label="sidebarItems[0].label"
        :to="sidebarItems[0].route"
        :is-collapsed="!isExpanded"
        class="mb-0.5"
      />
      <!-- <SidebarItem
        :label="'Inbox'"
        :icon="LucideInbox"
        class="mb-0.5"
        :is-collapsed="!isExpanded"
        :to="'/t/' + team + '/notifications'"
      >
        <template #right>
          <div
            v-if="isExpanded && notifCount.data > 0"
            class="flex items-center justify-start w-full duration-300 ease-in-out ml-2"
          >
            <span class="text-xs text-ink-gray-4 ease-in ml-auto">
              {{ notifCount.data }}
            </span>
          </div>
        </template>
      </SidebarItem> -->
      <template v-for="item in sidebarItems.slice(1)" :key="item.label">
        <SidebarItem
          v-if="item.label !== __('Nhóm')"
          :icon="item.icon"
          :label="item.label"
          :to="item.route"
          :is-collapsed="!isExpanded"
          class="mb-0.5"
        />
        <div v-else-if="item.label === __('Nhóm')" class="mb-0.5 relative team-dropdown-container">
          <button
            @click="toggleTeamDropdown"
            class="flex h-7 w-full cursor-pointer items-center rounded text-ink-gray-7 duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-outline-gray-3 hover:bg-surface-gray-2"
            :class="{ 'bg-surface-selected shadow-sm': showTeamDropdown }"
          >
            <div class="flex w-full items-center justify-between duration-300 ease-in-out p-2">
              <div class="flex items-center">
                <span class="grid h-4.5 w-4.5 flex-shrink-0 place-items-center">
                  <component
                    :is="item.icon"
                    class="size-4 text-ink-gray-7"
                  />
                </span>
                <span
                  v-if="isExpanded"
                  class="ml-2 flex-1 flex-shrink-0 text-sm duration-300 ease-in-out"
                >
                  {{ item.label }}
                </span>
              </div>
              <LucideChevronDown 
                v-if="isExpanded"
                class="h-4 w-4 text-ink-gray-5 transition-transform duration-200"
                :class="{ 'rotate-180': showTeamDropdown }"
              />
            </div>
          </button>
          
          <!-- Simple Dropdown List -->
          <div
            v-if="showTeamDropdown && isExpanded"
            class="mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto z-50"
          >
            <!-- Teams List -->
            <div
              v-for="teamItem in teamList"
              :key="teamItem.name"
              @click="selectTeam(teamItem)"
              class="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
              :class="{ 'bg-blue-50 text-blue-600': team === teamItem.name }"
            >
              <span class="text-sm">{{ teamItem.title }}</span>
            </div>
            
            <!-- Separator -->
            <div v-if="teamList.length > 0" class="border-t border-gray-200 my-1"></div>
            
            <!-- Create Team Button -->
            <div
              @click="createNewTeam"
              class="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer text-gray-600 hover:text-gray-800"
            >
              <LucidePlus class="h-4 w-4 mr-2" />
              <span class="text-sm">Tạo nhóm</span>
            </div>
          </div>
        </div>
      </template>
    </div>
    <div class="mt-auto">
      <StorageBar :is-expanded="isExpanded" />
    </div>

    <!-- Create Team Modal -->
    <Dialog
      v-model="showCreateTeamModal"
      :options="{
        title: 'Tạo nhóm mới',
        size: '2xl',
      }"
    >
      <template #body-content>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Tên nhóm
            </label>
            <FormControl
              v-model="newTeamName"
              type="text"
              placeholder="Nhập tên nhóm..."
              :disabled="createTeam.loading"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <Button
          variant="ghost"
          @click="showCreateTeamModal = false"
          :disabled="createTeam.loading"
        >
          Hủy
        </Button>
        <Button
          variant="solid"
          @click="handleCreateTeam"
          :loading="createTeam.loading"
        >
          Tạo nhóm
        </Button>
      </template>
    </Dialog>

  </div>
</template>
<script setup>
import PrimaryDropDown from "./PrimaryDropdown.vue"
import SidebarItem from "@/components/SidebarItem.vue"
import StorageBar from "./StorageBar.vue"

import { notifCount } from "@/resources/permissions"
import { getTeams } from "@/resources/files"
import { Dropdown, Button, Autocomplete, Dialog, FormControl, createResource } from "frappe-ui"

import { computed, ref, onMounted, onUnmounted } from "vue"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { toast } from "@/utils/toasts"
import LucideClock from "~icons/lucide/clock"
import ArrowLeftFromLine from "~icons/lucide/arrow-left-from-line"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideUsers from "~icons/lucide/users"
import LucideTrash from "~icons/lucide/trash"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
import LucideCommand from "~icons/lucide/command"
import LucideInbox from "~icons/lucide/inbox"
import LucideChevronDown from "~icons/lucide/chevron-down"
import LucidePlus from "~icons/lucide/plus"

defineEmits(["toggleMobileSidebar", "showSearchPopUp"])
const store = useStore()
const route = useRoute()
notifCount.fetch()

// Team dropdown state
const showTeamDropdown = ref(false)

// Create team modal state
const showCreateTeamModal = ref(false)
const newTeamName = ref("")

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
      // Navigate to new team
      window.location.href = `/drive/t/${data}/team`
    }
  },
  onError: (error) => {
    toast("Không thể tạo nhóm. Vui lòng thử lại.")
    console.error("Create team error:", error)
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
    if (target) window.location.href = `/drive/t/${target.name}/team`
  },
})
const teamAutocompleteOptions = computed(() =>
  teamList.value.map((t) => ({ label: t.title }))
)

const teamDropdownOptions = computed(() =>
  teamList.value.map((t) => ({ 
    label: t.title, 
    onClick: () => {
      window.location.href = `/drive/t/${t.name}/team`
    }
  }))
)

const sidebarItems = computed(() => {
  const items = [
    {
      label: __("Trang chủ"),
      route: `/t/${team.value}/`,
      icon: LucideHome,
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
      label: __("Nhóm"),
      route: `/t/${team.value}/team`,
      icon: LucideBuilding2,
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

// Team dropdown methods
const toggleTeamDropdown = () => {
  showTeamDropdown.value = !showTeamDropdown.value
}

const selectTeam = (team) => {
  showTeamDropdown.value = false
  window.location.href = `/drive/t/${team.name}/team`
}

const createNewTeam = () => {
  showTeamDropdown.value = false
  showCreateTeamModal.value = true
}

const handleCreateTeam = () => {
  if (!newTeamName.value?.trim()) {
    toast("Vui lòng nhập tên nhóm.")
    return
  }
  createTeam.submit()
}

// Click outside to close dropdown
const handleClickOutside = (event) => {
  const dropdown = event.target.closest('.team-dropdown-container')
  if (!dropdown) {
    showTeamDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

</script>
