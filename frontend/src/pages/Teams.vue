<template>
  <div class="flex h-screen w-full overflow-hidden sm:bg-surface-menu-bar">
    <div class="w-full overflow-auto">
      <div class="relative h-full">
        <div class="relative z-10 mx-auto pt-8 sm:w-max sm:pt-20">
          <div
            class="flex flex-col items-center"
            @dblclick="window.location.href = '/f-login'"
          >
            <FrappeDriveLogo class="inline-block h-12 w-12 rounded-md" />
          </div>

          <div
            class="relative mx-auto w-full bg-surface-white px-4 py-8 sm:mt-6 sm:w-112 sm:rounded-2xl sm:px-6 sm:py-6 sm:shadow-2xl"
          >
            <div class="text-sm absolute top-3 right-3 flex gap-1.5">
              <LucideLogOut class="w-3 h-3 my-auto" />
              <a
                href="#"
                @click="$store.dispatch('logout')"
                >Log out</a
              >
            </div>
            <h2 class="grow font-bold font-xl text-center mb-4">
              Welcome, {{ $store.state.user.fullName }}
            </h2>

            <div class="py-3">
              <p class="font-bold text-lg mb-3">Teams</p>
              <p
                v-if="!getTeams.data || !Object.values(getTeams.data).length"
                class="text-center text-sm flex flex-col gap-4"
              >
                You haven't joined any teams yet.
              </p>
              <ul
                v-else
                class="ms-1"
              >
                <li
                  v-for="team in Object.values(getTeams?.data)"
                  :key="team.id"
                  class="mb-3"
                >
                  <div class="flex justify-between">
                    <div class="flex flex-col">
                      {{ team.title }}
                      <span class="text-sm"
                        >{{ team.users.length }} members</span
                      >
                    </div>
                    <router-link
                      class="my-auto"
                      :to="{ name: 'Team', params: { team: team.name } }"
                    >
                      <LucideFolderOpenDot class="size-4" />
                    </router-link>
                  </div>
                </li>
              </ul>
            </div>
            <div class="py-3">
              <p class="font-bold text-lg mb-3">Invites</p>
              <p
                v-if="!getInvites?.data?.length"
                class="text-center text-sm"
              >
                No invites found.
              </p>
              <li
                v-for="(invite, index) in getInvites?.data"
                :key="invite.name"
                class="w-full flex justify-between mb-2 ms-1"
              >
                <div class="flex flex-col">
                  <span class="text-md">{{ invite.team_name }}</span>
                  <span class="text-sm"
                    >{{
                      invite.status === "Proposed" ? "Requested" : "Sent"
                    }}
                    at {{ formatDate(invite.creation) }}</span
                  >
                </div>
                <div class="flex gap-2">
                  <Tooltip text="You requested an invite from this team.">
                    <Badge
                      v-if="invite.status === 'Proposed'"
                      class="my-auto mr-2"
                      theme="orange"
                    >
                      Requested
                    </Badge>
                  </Tooltip>
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
                      acceptInvite.submit({ key: invite.name, redirect: 0 })
                    "
                  >
                    <LucideCheck class="size-4" />
                  </Button>
                </div>
              </li>
            </div>
            <div
              v-if="
                !getInvites?.data?.length &&
                getTeams.data &&
                !Object.values(getTeams.data).length
              "
              class="text-sm font-semibold mt-2"
            >
              <hr />
              <div class="flex gap-2 w-fit mx-auto mt-4">
                <LucidePlaneTakeoff class="w-3 h-3 my-auto" />
                <router-link
                  :to="{
                    name: 'Setup',
                  }"
                >
                  Get started
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { getTeams } from "@/resources/files"
import { Badge, Tooltip } from "frappe-ui"
import { getInvites, rejectInvite, acceptInvite } from "@/resources/permissions"
import { useStore } from "vuex"
import { formatDate } from "@/utils/format"
import { computed } from "vue"
import LucideFolderOpenDot from "~icons/lucide/folder-open-dot"
import LucidePlaneTakeoff from "~icons/lucide/plane-takeoff"

const store = useStore()
const email = computed(() => store.state.user.id)
getTeams.fetch()
getInvites.fetch({ email: email.value })
</script>
