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
            class="mx-auto w-full bg-surface-white px-4 py-8 sm:mt-6 sm:w-112 sm:rounded-2xl sm:px-6 sm:py-6 sm:shadow-2xl"
          >
            <div class="mb-7.5 text-center">
              <p class="mb-2 text-2xl font-semibold leading-6 text-ink-gray-9">
                Welcome to Drive
              </p>
              <p
                class="break-words text-base font-normal leading-[21px] text-ink-gray-7"
              >
                We're glad you're here.
              </p>
            </div>

            <div
              v-if="domainTeams.loading"
              class="flex justify-center py-8"
            >
              <div
                class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"
              />
            </div>
            <div class="flex flex-col text-md gap-2">
              <p>
                We noticed that you are on a
                <strong>corporate domain</strong>.
              </p>
              <p v-if="domainTeams.data.length">
                Do you want to create a personal account, or request to join the
                team (<strong>{{ domainTeams.data[0].title }}</strong
                >) associated with your domain?
              </p>
              <p v-else>
                Do you want to create a personal account, or create a team with
                your domain?
              </p>
              <FormControl
                v-if="typeof team_name === 'string'"
                v-model="team_name"
                label="Team Name"
                class="py-2"
                type="text"
                required
              />
              <div class="flex justify-between mt-3">
                <Button
                  variant="subtle"
                  class="w-100"
                  @click="createPersonalTeam.submit()"
                >
                  Create Personal
                </Button>
                <Button
                  v-if="domainTeams.data.length"
                  variant="solid"
                  @click="
                    requestInvite.submit({
                      team: domainTeams.data[0].name,
                    }),
                      $router.replace({ path: '/drive/teams' })
                  "
                >
                  Join {{ domainTeams.data[0].title }}
                </Button>
                <Button
                  v-else
                  variant="solid"
                  @click="
                    typeof team_name === 'string'
                      ? createPersonalTeam.submit({ team_name, email })
                      : (team_name = '')
                  "
                >
                  Create Team
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { createResource, FormControl } from "frappe-ui"
import { ref, computed } from "vue"
import FrappeDriveLogo from "../components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

const route = useRoute()
const store = useStore()
const team_name = ref(null)
const email = computed(() => store.state.user.id)

const domainTeams = createResource({
  url: "drive.api.product.get_domain_teams",
  auto: true,
  params: {
    domain: email.value.split("@").slice(-1)[0],
  },
})

const createPersonalTeam = createResource({
  url: "drive.api.product.create_personal_team",
  makeParams: () => ({
    team_name: team_name.value,
    email: email.value,
  }),
  onSuccess: (data) => {
    if (data) {
      window.location.replace("/drive/t/" + data)
    } else {
      window.location.reload()
    }
  },
  onError() {
    toast("Failed to create team. Please try again.")
  },
})

const requestInvite = createResource({
  url: "drive.api.product.request_invite",
  onSuccess: () => {
    window.location.replace("/drive/teams")
  },
})
</script>
