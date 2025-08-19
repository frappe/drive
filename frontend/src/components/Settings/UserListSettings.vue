<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("Người dùng") }}
    </h1>
    <Button
      v-if="isAdmin?.data"
      variant="solid"
      icon-left="plus"
      class="ml-auto mr-4"
      @click="showInvite = true"
    >
      {{ __("Mời") }}
    </Button>
  </div>

  <Tabs :tabs>
    <template #tab-panel="{ tab }">
      <template v-if="tab.label === 'Members'">
        <div class="flex flex-col items-stretch justify-start overflow-y-auto">
          <div
            v-for="(user, index) in allUsers?.data"
            :key="user.user_name"
          >
            <div
              v-if="index > 0"
              class="w-[95%] mx-auto h-px border-t border-outline-gray-modals"
            />
            <div class="flex items-center justify-start py-2 pl-2 pr-4 gap-x-3">
              <Avatar
                :image="user.user_image"
                :label="user.full_name"
                size="lg"
              />
              <div class="flex flex-col">
                <span class="text-base text-ink-gray-8">{{
                  user.full_name
                }}</span>
                <span class="text-xs text-ink-gray-6">{{ user.email }}</span>
              </div>
              <Dropdown
                v-if="isAdmin.data && user.name != $store.state.user.id"
                v-slot="{ open }"
                :options="accessOptions"
                placement="right"
                class="ml-auto text-base text-ink-gray-6"
              >
                <Button
                  variant="ghost"
                  @click="selectedUser = user"
                >
                  {{
                    __(
                      user.access_level == 2
                        ? "Quản lý"
                        : user.access_level == 1
                        ? "Người dùng"
                        : "Khách"
                    )
                  }}
                  <template #suffix>
                    <LucideChevronDown
                      class="size-4 text-ink-gray-6"
                      :class="{ '[transform:rotateX(180deg)]': open }"
                    />
                  </template>
                </Button>
              </Dropdown>
              <span
                v-else
                class="ml-auto text-base text-ink-gray-6"
                >{{
                  __(
                    user.access_level == 2
                      ? "Quản lý"
                      : user.access_level == 1
                      ? "Người dùng"
                      : "Khách"
                  )
                }}
                <template v-if="user.name === $store.state.user.id"
                  >(bạn)</template
                >
              </span>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div
          v-if="!invites?.data || !invites.data.length"
          class="text-center text-p-sm py-4"
        >
          Không tìm thấy lời mời nào.
        </div>
        <div
          v-for="(invite, index) in invites?.data"
          :key="invite.name"
        >
          <div
            v-if="index > 0"
            class="w-[95%] mx-auto h-px border-t border-outline-gray-modals"
          />
          <div class="flex items-center justify-start py-2 pl-2 pr-4 gap-x-3">
            <div class="flex justify-between w-full">
              <span class="text-base my-auto text-ink-gray-8">{{
                invite.email
              }}</span>
              <div class="flex">
                <Tooltip
                  :text="
                    invite.status === 'Proposed'
                      ? 'Một người từ domain của bạn đã tham gia Drive.'
                      : 'Lời mời này đã được gửi từ nhóm của bạn.'
                  "
                >
                  <Badge
                    :theme="invite.status === 'Pending' ? 'blue' : 'orange'"
                    variant="subtle"
                    class="my-auto mr-2"
                    size="sm"
                  >
                    {{ __(invite.status) }}
                  </Badge>
                </Tooltip>
                <div class="flex gap-2">
                  <Button
                    :variant="
                      invite.status === 'Proposed' ? 'ghost' : 'outline'
                    "
                    class="my-auto"
                    @click="
                      rejectInvite.submit({ key: invite.name }),
                        invites.data.splice(index, 1)
                    "
                  >
                    <LucideX
                      v-if="invite.status === 'Proposed'"
                      class="size-4"
                    />
                    <LucideTrash
                      v-else
                      class="size-4"
                    />
                  </Button>

                  <Button
                    v-if="invite.status === 'Proposed'"
                    class="my-auto"
                    variant="outline"
                    @click="
                      acceptInvite.submit({ key: invite.name, redirect: 0 }),
                        invites.data.splice(index, 1)
                    "
                  >
                    <LucideCheck class="size-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div></div
      ></template>
    </template>
  </Tabs>

  <Dialog
    v-model="showInvite"
    :options="{
      title: 'Mời mọi người đến ' + getTeams.data[team].title,
      size: 'lg',
      actions: [
        {
          label: 'Gửi lời mời',
          variant: 'solid',
          disabled: !emailTest().length && !invited.length,
          loading: inviteUsers.loading,
          onClick: () => {
            extractEmails()
            showInvite = false
            inviteUsers.submit({
              emails: invited.join(','),
              team,
            })
          },
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex items-start justify-start gap-4">
        <div class="flex flex-wrap gap-1 rounded w-full bg-surface-gray-2 p-2 relative" ref="inviteDropdownContainer">
          <Button
            v-for="(email, idx) in invitedEmailsArray"
            :key="email"
            :label="email"
            variant="outline"
            class="shadow-sm"
          >
            <template #suffix>
              <LucideX
                class="h-4"
                stroke-width="1.5"
                @click.stop="() => removeInvitedEmail(idx)"
              />
            </template>
          </Button>
          <div class="min-w-[10rem] flex-1">
            <input
              v-model="inviteQuery"
              type="text"
              autocomplete="off"
              placeholder="Thêm người..."
              class="h-7 w-full rounded border-none bg-surface-gray-2 py-1.5 pl-2 pr-2 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
              @focus="handleInviteInputFocus"
              @input="handleInviteInputChange"
              @click="handleInviteInputFocus"
            />
          </div>
          
          <!-- Dropdown -->
          <div
            v-if="isInviteDropdownOpen"
            class="absolute top-full left-0 right-0 z-[4] rounded-lg bg-surface-modal text-base shadow-2xl mt-1"
          >
            <div class="max-h-[15rem] overflow-y-auto px-1.5 py-1.5">
              <div v-if="allSiteUsers.loading" class="px-2.5 py-1.5 text-ink-gray-5 text-sm cursor-not-allowed">
                Đang tải người dùng...
              </div>
              <div v-else-if="!filteredInviteUsers.length" class="px-2.5 py-1.5 text-ink-gray-5 text-sm cursor-not-allowed">
                {{ inviteQuery.length ? 'Không tìm thấy người dùng' : 'Không có người dùng khả dụng' }}
              </div>
              <div
                v-for="person in filteredInviteUsers"
                :key="person.email"
                class="flex flex-1 gap-2 overflow-hidden items-center rounded px-2.5 py-1.5 text-base text-ink-gray-7 hover:bg-surface-gray-3 cursor-pointer"
                @click="selectInviteUser(person)"
              >
                <Avatar
                  size="sm"
                  :label="person.full_name || person.email"
                  :image="person.user_image"
                  class="mr-2"
                />
                <span class="block truncate">
                  {{ person.email }}
                  <span v-if="person.full_name">
                    ({{ person.full_name }})
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
  <Dialog
    v-if="showRemove"
    v-model="showRemove"
    :options="{
      title: __('Are you sure?'),
      size: 'md',
      message: `${__('Removing')} ${selectedUser.full_name} ${__('will completely revoke their access to your team. You can always add them back using the same email ID.')}.`,
      actions: [
        {
          variant: 'solid',
          theme: 'red',
          label:
            __('I confirm that I want to remove') + ' ' + selectedUser.full_name + '.',
          loading: removeUser.loading,
          onClick: () => {
            removeUser.submit({
              user_id: selectedUser.name,
              team,
            })
            allUsers.data.splice(allUsers.data.indexOf(selectedUser), 1)
            showRemove = false
          },
        },
      ],
    }"
  />
</template>

<script setup>
import { getTeams } from "@/resources/files"
import { acceptInvite, allSiteUsers, allUsers, rejectInvite } from "@/resources/permissions"
import { toast } from "@/utils/toasts"
import {
  Avatar,
  Badge,
  Dialog,
  Dropdown,
  Tabs,
  Tooltip,
  createResource,
} from "frappe-ui"
import { computed, h, onMounted, onUnmounted, ref } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import LucideMail from "~icons/lucide/mail"
import LucideUsers from "~icons/lucide/users"

const route = useRoute()
const store = useStore()
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

const dialog = ref(null)
const selectedUser = ref(null)
const invited = ref("")
const emailInput = ref("")
const showInvite = ref(false)
const showRemove = ref(false)

// Dropdown variables for invite 
const inviteQuery = ref("")
const isInviteDropdownOpen = ref(false)
const inviteDropdownContainer = ref(null)

const tabs = [
  {
    label: __("Members"),
    icon: h(LucideUsers, { class: "size-4" }),
  },
  {
    label: __("Invites"),
    icon: h(LucideMail, { class: "size-4" }),
  },
]

const updateAccess = (level) => {
  selectedUser.value.access_level = level
  updateUserAccess.submit({
    team: team.value,
    user_id: selectedUser.value.name,
    access_level: level,
  })
}
const accessOptions = [
  {
    label: __("Manager"),
    onClick: () => updateAccess(2),
  },
  {
    label: __("User"),
    onClick: () => updateAccess(1),
  },
  // {
  //   label: "Guest",
  //   onClick: () => updateAccess(0),
  // },
  {
    label: __("Remove"),
    class: "text-ink-red-3",
    component: () =>
      h(
        "button",
        {
          class: [
            "group flex w-full items-center text-ink-red-3 rounded-md px-2 py-2 text-sm",
          ],
          onClick: () => (showRemove.value = true),
        },
        __("Remove")
      ),
  },
]
allUsers.fetch({ team: team.value })

// Invite dropdown computed properties
const allInviteUsersData = computed(() => allSiteUsers.data || [])

const invitedEmailsArray = computed(() => {
  return invited.value ? invited.value.split(',').map(e => e.trim()).filter(e => e) : []
})

const filteredInviteUsers = computed(() => {
  const allUsers = allInviteUsersData.value || []
  if (!allUsers.length) return []

  const currentUserId = store.state.user.id
  const availableUsers = allUsers.filter(k => k.name !== currentUserId)
  
  // Convert invited string to array for filtering
  const invitedEmails = invited.value ? invited.value.split(',').map(e => e.trim()) : []

  if (!inviteQuery.value.trim()) {
    return availableUsers.filter(user => !invitedEmails.includes(user.email))
  }

  const regex = new RegExp(inviteQuery.value.trim(), "i")
  return availableUsers
    .filter((k) => {
      const email = k.email || ''
      const fullName = k.full_name || ''
      return regex.test(email) || regex.test(fullName)
    })
    .filter(user => !invitedEmails.includes(user.email))
})

function emailTest() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailInput.value
    .split(/,|\s/)
    .filter((email) => email)
    .filter((email) => emailRegex.test(email))
    .filter((email) => !invited.value.includes(email))
}

function extractEmails() {
  invited.value = [...invited.value, ...emailTest()]
  emailInput.value = ""
}

// Dropdown methods
const handleInviteInputFocus = () => {
  isInviteDropdownOpen.value = true
}

const handleInviteInputChange = () => {
  isInviteDropdownOpen.value = true
}

const selectInviteUser = (person) => {
  // Add email to invited string
  if (invited.value) {
    invited.value += ',' + person.email
  } else {
    invited.value = person.email
  }
  inviteQuery.value = ''
  isInviteDropdownOpen.value = false
}

const handleInviteClickOutside = (event) => {
  if (!isInviteDropdownOpen.value) return
  
  if (inviteDropdownContainer.value && !inviteDropdownContainer.value.contains(event.target)) {
    isInviteDropdownOpen.value = false
  }
}

const removeInvitedEmail = (index) => {
  const emails = invitedEmailsArray.value
  emails.splice(index, 1)
  invited.value = emails.join(',')
}

const isAdmin = createResource({
  url: "drive.api.permissions.is_admin",
  params: { team: team.value },
  auto: true,
})

const inviteUsers = createResource({
  url: "drive.api.product.invite_users",
  onSuccess: () => {
    invites.fetch()
    toast("Invite sent!")
  },
})

const invites = createResource({
  url: "drive.api.product.get_team_invites",
  auto: true,
  params: { team: team.value },
})

const removeUser = createResource({
  url: "drive.api.product.remove_user",
})

const updateUserAccess = createResource({
  url: "drive.api.product.set_user_access",
})

// Lifecycle hooks
onMounted(() => {
  allSiteUsers.fetch().catch(error => {
    console.error("Error fetching all site users:", error)
  })
  
  document.addEventListener('mousedown', handleInviteClickOutside)
  document.addEventListener('click', handleInviteClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleInviteClickOutside)
  document.removeEventListener('click', handleInviteClickOutside)
})
</script>
