<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("Teams") }}
    </h1>
    <Button
      variant="solid"
      icon="plus"
      class="ml-auto mr-4"
      @click="showAddTeam = true"
    >
      {{ __("New team") }}
    </Button>
  </div>
  <Alert
    v-if="invite"
    type="info"
    :icon="LucideMail"
    class="mb-4"
  >
    <template #actions>
      <Button
        :variant="invite.status === 'Pending' ? 'ghost' : 'outline'"
        class="my-auto"
        @click="
          rejectInvite.submit({ key: invite.name }),
            getInvites.data.splice(index, 1)
        "
      >
        <LucideX
          v-if="invite.status === 'Pending'"
          class="size-4"
        />
        <LucideTrash
          v-else
          class="size-4"
        />
      </Button>

      <Button
        v-if="invite.status === 'Pending'"
        class="my-auto"
        variant="outline"
        @click="
          acceptInvite.submit(
            { key: invite.name, redirect: 0 },
            {
              onSuccess: () => {
                getTeams.fetch()
                getInvites.fetch()
              },
            }
          )
        "
      >
        <LucideCheck class="size-4" />
      </Button>
    </template>
    <div class="py-1 flex justify-between">
      <div>
        You have an invite to join
        <span class="font-medium">{{ invite.team_name }}</span
        >.
      </div>
    </div>
  </Alert>
  <div
    class="flex gap-2 mb-2"
    v-if="team"
  >
    <Combobox
      :options="
        Object.values(getTeams.data).map((k) => ({
          label: k.title,
          value: k.name,
          icon: icons[k.icon || 'building'],
        }))
      "
      v-model="team"
    />
    <Dropdown
      :button="{
        variant: 'ghost',
        icon: LucideMoreVertical,
      }"
      :options="
        dynamicList([
          {
            label: 'Invite',
            icon: LucideMail,
            onClick: () => (showInvite = true),
            cond: isAdmin.data,
          },
          {
            label: 'Edit',
            icon: LucidePencil,
            onClick: () => (showEditTeam = true),
          },
          {
            label: 'Leave',
            icon: LucideLogOut,
            onClick: () => leaveTeam.submit({ team }),
          },
        ])
      "
    />
  </div>
  <Tabs
    v-if="team"
    :tabs
    v-model="tabIndex"
  >
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
              <div
                v-if="isAdmin.data && user.name != $store.state.user.id"
                class="ml-auto"
              >
                <Dropdown
                  v-slot="{ open }"
                  :options="accessOptions"
                  placement="right"
                >
                  <Button
                    variant="ghost"
                    @click="selectedUser = user"
                  >
                    {{
                      __(
                        user.access_level == 2
                          ? "Manager"
                          : user.access_level == 1
                          ? "User"
                          : "Guest"
                      )
                    }}
                    <template #suffix>
                      <LucideChevronDown
                        class="size-4 text-ink-gray-6"
                        :class="{
                          '[transform:rotateX(180deg)]': open,
                        }"
                      />
                    </template>
                  </Button>
                </Dropdown>
              </div>
              <span
                v-else
                class="ml-auto text-base text-ink-gray-6"
                >{{
                  __(
                    user.access_level == 2
                      ? "Manager"
                      : user.access_level == 1
                      ? "User"
                      : "Guest"
                  )
                }}
                <template v-if="user.name === $store.state.user.id"
                  >(you)</template
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
          No invites found.
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
              <div class="flex flex-col gap-0.5">
                <span class="text-base my-auto text-ink-gray-8">{{
                  invite.email
                }}</span>
                <span class="text-xs text-ink-gray-5"
                  >Invited by <UserTooltip :email="invite.owner" />
                </span>
              </div>
              <div class="flex">
                <Tooltip
                  :text="
                    invite.status === 'Proposed'
                      ? 'A person from your domain has joined Drive.'
                      : 'This invite was sent from your team.'
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
                    :loading="acceptInvite.loading"
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
  <div>
    <div
      v-if="!team"
      class="text-center text-p-sm py-4"
    >
      No teams yet. Create one to get started.
    </div>
  </div>

  <Dialog
    v-model="showInvite"
    :options="{
      title: 'Invite people to ' + teamData.title,
      size: 'lg',
      actions: [
        {
          label: 'Send Invitation',
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
        <div class="flex flex-wrap gap-1 rounded w-full bg-surface-gray-2 p-2">
          <Button
            v-for="(email, idx) in invited"
            :key="email"
            :label="email"
            variant="outline"
            class="shadow-sm"
          >
            <template #suffix>
              <LucideX
                class="h-4"
                stroke-width="1.5"
                @click.stop="() => invited.splice(idx, 1)"
              />
            </template>
          </Button>
          <div class="min-w-[10rem] flex-1">
            <input
              v-model="emailInput"
              type="text"
              autocomplete="off"
              placeholder="Enter email address"
              class="h-7 w-full rounded border-none bg-surface-gray-2 py-1.5 pl-2 pr-2 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
              @keydown="isValidEmail"
              @keydown.enter.capture.stop="extractEmails"
              @keydown.space.prevent.stop="extractEmails"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
  <Dialog
    v-if="showRemove"
    v-model="showRemove"
    :options="{
      title: 'Are you sure?',
      size: 'md',
      message: `Removing ${selectedUser.full_name} will completely revoke their access to your team. You can always add them back using the same email ID.`,
      actions: [
        {
          variant: 'solid',
          theme: 'red',
          label:
            'I confirm that I want to remove ' + selectedUser.full_name + '.',
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
  <Dialog
    v-model="showAddTeam"
    :options="{ title: __('New Team'), size: 'sm' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-2">
        <FormControl
          required
          :label="__('Name')"
          type="input"
          v-model="teamName"
        />
        <div>
          <FormLabel
            :label="__('Icon')"
            class="mb-1"
          />
          <Combobox
            :options="
              Object.keys(icons).map((k) => ({
                label: k
                  .split('-')
                  .map((i) => i.charAt(0).toUpperCase() + i.slice(1))
                  .join(' '),
                value: k,
                icon: icons[k],
              }))
            "
            v-model="selectedIcon"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        :disabled="!teamName.trim().length"
        variant="solid"
        @click="
          createTeam.submit(
            { team_name: teamName, icon: selectedIcon },
            {
              onSuccess: () => {
                showAddTeam = false
                teamName = ''
                selectedIcon = ''
                getTeams.fetch()
              },
            }
          )
        "
      >
        {{ __("Add") }}
      </Button>
    </template>
  </Dialog>
  <Dialog
    v-model="showEditTeam"
    :options="{ title: __('Edit ' + teamData.title), size: 'sm' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-2">
        <FormControl
          required
          :label="__('Name')"
          type="input"
          v-model="teamName"
        />
        <div>
          <FormLabel
            :label="__('Icon')"
            class="mb-1"
          />
          <Combobox
            :options="
              Object.keys(icons).map((k) => ({
                label: k
                  .split('-')
                  .map((i) => i.charAt(0).toUpperCase() + i.slice(1))
                  .join(' '),
                value: k,
                icon: icons[k],
              }))
            "
            v-model="selectedIcon"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        :disabled="!teamName.trim().length"
        variant="solid"
        class="w-full"
        @click="
          editTeam.submit(
            { team, team_name: teamName, icon: selectedIcon },
            {
              onSuccess: () => {
                showEditTeam = false
                teamName = ''
                selectedIcon = ''
                getTeams.fetch()
              },
            }
          )
        "
      >
        {{ __("Edit") }}
      </Button>
    </template>
  </Dialog>
</template>

<script setup>
import { h, computed } from "vue"
import { getTeams } from "@/resources/files"
import icons from "@/utils/icons"
import {
  getInvites,
  rejectInvite,
  acceptInvite,
  createTeam,
} from "@/resources/permissions"
import {
  Avatar,
  Dropdown,
  Dialog,
  Badge,
  Tabs,
  Tooltip,
  createResource,
  FormControl,
  Combobox,
  FormLabel,
} from "frappe-ui"
import { allUsers } from "@/resources/permissions"
import { ref, watch } from "vue"
import { toast } from "@/utils/toasts"
import { useRoute } from "vue-router"
import LucideMail from "~icons/lucide/mail"
import LucideUsers from "~icons/lucide/users"
import LucideMoreVertical from "~icons/lucide/more-vertical"
import LucideLogOut from "~icons/lucide/log-out"
import LucidePencil from "~icons/lucide/pencil"
import router from "@/router"
import Alert from "@/components/Alert.vue"
import UserTooltip from "@/components/UserTooltip.vue"
import { dynamicList } from "../../utils/files"

const route = useRoute()
const tabIndex = ref(0)
getTeams.fetch()
const team = ref(
  route.params.team || getTeams.data ? Object.keys(getTeams.data)[0] : null
)
const teamData = computed(() => getTeams.data?.[team.value] || {})
watch(
  team,
  (team) => {
    allUsers.fetch({ team })
    tabIndex.value = 0
  },
  { immediate: true }
)
const selectedUser = ref(null)
const invited = ref("")
const emailInput = ref("")
const showInvite = ref(false)
const showRemove = ref(false)

// New team
const showAddTeam = ref(false)
const showEditTeam = ref(false)
const teamName = ref("")
const selectedIcon = ref("")
watch(showEditTeam, (val) => {
  if (val) {
    teamName.value = teamData.value.title
    selectedIcon.value = teamData.value.icon
  }
})
const editTeam = createResource({
  url: "drive.api.product.edit_team",
})
const leaveTeam = createResource({
  url: "drive.api.product.leave_team",
  onSuccess: () => {
    getTeams.fetch()
    team.value = getTeams.data ? Object.keys(getTeams.data)[0] : null
    router.push({ name: "Team", params: { team: team.value } })
    toast("You have left the team.")
  },
})

const tabs = [
  {
    label: "Members",
    icon: h(LucideUsers, { class: "size-4" }),
  },
  {
    label: "Invites",
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
    label: "Manager",
    onClick: () => updateAccess(2),
  },
  {
    label: "User",
    onClick: () => updateAccess(1),
  },
  {
    label: "Guest",
    onClick: () => updateAccess(0),
  },
  {
    label: "Remove",
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
        "Remove"
      ),
  },
]

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
getInvites.fetch()
const invite = computed(() =>
  getInvites.data?.length ? getInvites.data[0] : null
)

const removeUser = createResource({
  url: "drive.api.product.remove_user",
})

const updateUserAccess = createResource({
  url: "drive.api.product.set_user_access",
})
</script>
