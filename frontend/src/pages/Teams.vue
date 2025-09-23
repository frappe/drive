<template>
  <div
    class="mx-auto w-full bg-surface-white dark:bg-surface-gray-2 px-4 py-8 mt-6 w-112 rounded-2xl p-6 md:shadow-2xl flex flex-col gap-4"
  >
    <div class="text-sm absolute top-5 right-5 flex gap-1.5 text-ink-gray-8">
      <LucideLogOut class="w-3 h-3 my-auto" />
      <a
        href="#"
        @click="$store.dispatch('logout')"
        >Log out</a
      >
    </div>
    <div class="flex flex-col items-center">
      <FrappeDriveLogo class="inline-block h-12 w-12 rounded-md" />
    </div>

    <h2 class="font-bold text-lg text-center text-ink-gray-8">
      Welcome, {{ $store.state.user.fullName.split(" ")[0] }}
    </h2>
    <div>
      <p class="font-semibold text-sm text-ink-gray-8 mb-1 ms-1">Teams</p>
      <ul class="flex flex-col">
        <template
          v-for="team in Object.values(getTeams?.data)"
          :key="team.id"
        >
          <router-link
            class="my-auto"
            :to="{ name: 'Team', params: { team: team.name } }"
          >
            <li>
              <div
                class="flex justify-between text-ink-gray-7 hover:bg-surface-gray-3 py-1.5 px-2 rounded group"
              >
                <div class="flex flex-col">
                  {{ team.title }}
                  <span class="text-xs text-ink-gray-6"
                    >{{ team.users.length }} members</span
                  >
                </div>

                <LucideFolderOpenDot
                  class="size-4 self-center hidden group-hover:block"
                />
              </div>
            </li>
          </router-link>
        </template>
      </ul>
    </div>
    <div v-if="getInvites?.data?.length">
      <p class="font-semibold text-sm mb-3">Invites</p>
      <li
        v-for="(invite, index) in getInvites?.data"
        :key="invite.name"
        class="w-full flex justify-between mb-2 ms-1"
      >
        <div class="flex flex-col">
          <span class="text-md">{{ invite.team_name }}</span>
          <span class="text-sm"
            >{{ invite.status === "Proposed" ? "Requested" : "Sent" }} at
            {{ formatDate(invite.creation) }}</span
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
              acceptInvite.submit(
                { key: invite.name },
                {
                  onSuccess: (data) => {
                    if (data) window.location.replace(data)
                    else toast('Added to the team')
                  },
                }
              )
            "
          >
            <LucideCheck class="size-4" />
          </Button>
        </div>
      </li>
    </div>
  </div>
</template>
<script setup>
import { getTeams } from "@/resources/files"
import { Badge, Tooltip } from "frappe-ui"
import { getInvites, rejectInvite, acceptInvite } from "@/resources/permissions"
import { useStore } from "vuex"
import { formatDate } from "@/utils/format"
import { computed, watch } from "vue"
import LucideFolderOpenDot from "~icons/lucide/folder-open-dot"
import { useRouter } from "vue-router"

const router = useRouter()
getInvites.fetch()

watch(
  [getInvites, getTeams],
  ([a, b]) => {
    if (!a.data || !b.data) return
    if (!Object.keys(a.data).length && !Object.keys(b.data).length) {
      router.replace({ name: "Setup" })
    }
  },
  { immediate: true }
)
</script>
