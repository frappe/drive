<template>
  <div class="flex h-screen w-full overflow-hidden sm:bg-gray-50">
    <div class="w-full overflow-auto">
      <div class="relative h-full">
        <div class="relative z-10 mx-auto pt-8 sm:w-max sm:pt-20">
          <!-- logo -->
          <div
            class="flex flex-col items-center"
            @dblclick="window.location.href = '/f-login'"
          >
            <FrappeDriveLogo class="inline-block h-12 w-12 rounded-md" />
          </div>
          <!-- card -->
          <div
            class="mx-auto w-full bg-white px-4 py-8 sm:mt-6 sm:w-112 sm:rounded-2xl sm:px-6 sm:py-6 sm:shadow-2xl"
          >
            <div class="mb-7.5 text-center">
              <p class="mb-2 text-2xl font-semibold leading-6 text-gray-900">
                <template v-if="domainTeams.length">Welcome to Drive</template>
                <template v-else>{{
                  isLogin
                    ? "Log in to Drive"
                    : params.get("t")
                    ? "Join " + params.get("t")
                    : "Create a new account"
                }}</template>
              </p>
              <p
                class="break-words text-base font-normal leading-[21px] text-gray-700"
              >
                <template v-if="domainTeams.length"
                  >We're glad you're here.</template
                >
                <template v-else>
                  {{
                    !isLogin
                      ? params.get("t")
                        ? "Powered by Frappe Drive."
                        : "5 GB free - forever."
                      : "Welcome back!"
                  }}
                </template>
              </p>
            </div>
            <template v-if="domainTeams.length">
              <div class="flex flex-col ms-3 text-md gap-2">
                <p>
                  We noticed that you are on a
                  <strong>corporate domain</strong>.
                </p>
                <p v-if="domainTeams[0].title">
                  Do you want to create a personal account, or request to join
                  the team (<strong>{{ domainTeams[0].title }}</strong
                  >) associated with your domain?
                </p>
                <p v-else>
                  Do you want to create a personal account, or create a team
                  with your domain?
                </p>
                <FormControl
                  v-if="typeof team_name === 'string'"
                  label="Team Name"
                  class="py-2"
                  v-model="team_name"
                  type="text"
                  required
                />
                <div class="flex justify-between mt-3">
                  <Button
                    variant="subtle"
                    class="w-100"
                    @click="createPersonalTeam.submit()"
                    >Create Personal</Button
                  >
                  <Button
                    v-if="domainTeams[0].title"
                    variant="solid"
                    @click="
                      requestInvite.submit({
                        team: domainTeams[0].name,
                      }),
                        $router.go('/drive/teams')
                    "
                  >
                    Join {{ domainTeams[0].title }}
                  </Button>
                  <Button
                    v-else
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
            </template>
            <form v-else class="flex flex-col">
              <FormControl
                label="Email"
                v-model="email"
                type="email"
                placeholder="johndoe@mail.com"
                autocomplete="email"
                :disabled="otpRequested"
                required
              />
              <template v-if="otpValidated && !isLogin">
                <div class="mt-5 flex flex-row gap-5">
                  <FormControl
                    label="First Name"
                    type="text"
                    placeholder="Robin"
                    variant="outline"
                    v-model="first_name"
                    required
                  />
                  <FormControl
                    label="Last Name"
                    type="text"
                    placeholder="Hood"
                    variant="outline"
                    v-model="last_name"
                  />
                </div>
                <div class="!mt-6 flex gap-2">
                  <FormControl type="checkbox" v-model="terms_accepted" />
                  <label class="text-base">
                    I accept the
                    <Link
                      class="!text-gray-700"
                      to="https://frappecloud.com/policies"
                      target="_blank"
                    >
                      Terms and Policies
                    </Link>
                  </label>
                </div>
                <!-- Buttons -->
                <div class="mt-8 flex flex-col items-center gap-3">
                  <Button
                    :loading="signup?.loading"
                    :disabled="!first_name.length || !terms_accepted"
                    variant="solid"
                    class="w-full font-medium"
                    @click="signup.submit()"
                  >
                    Create Account
                  </Button>
                </div>
              </template>
              <div v-else-if="otpRequested">
                <FormControl
                  label="Verification code"
                  type="text"
                  class="mt-4"
                  placeholder="123456"
                  :disabled="verifyOTP.loading"
                  maxlength="6"
                  v-model="otp"
                  @keyup="
                    (e) =>
                      e.target.value.length === 6 &&
                      verifyOTP.submit({
                        account_request,
                        otp,
                      })
                  "
                  required
                />
                <ErrorMessage
                  class="mt-4 text-center"
                  :message="verifyOTP.error"
                />
                <Button
                  class="mt-4 w-full"
                  variant="solid"
                  :loading="verifyOTP.loading"
                  @click="
                    verifyOTP.submit({
                      account_request,
                      otp,
                    })
                  "
                >
                  Verify
                </Button>
                <Button
                  class="mt-2 w-full"
                  variant="outline"
                  :loading="sendOTP.loading"
                  @click="sendOTP.submit()"
                  :disabled="otpResendCountdown > 0"
                >
                  Resend verification code
                  {{
                    otpResendCountdown > 0
                      ? `in ${otpResendCountdown} seconds`
                      : ""
                  }}
                </Button>
              </div>
              <template v-else>
                <Button
                  class="mt-4"
                  :loading="sendOTP.loading"
                  variant="solid"
                  @click="sendOTP.submit({ email })"
                >
                  {{ isLogin ? "Login" : "Join" }}
                </Button>
                <p class="text-center text-sm my-3">
                  If this doesn't work, use
                  <a class="underline" href="/login">the old way</a>.
                </p>

                <div class="mt-6 border-t text-center">
                  <div class="-translate-y-1/2 transform">
                    <span
                      class="relative bg-white px-2 text-sm font-medium leading-8 text-gray-800"
                    >
                      or
                    </span>
                  </div>
                </div>
                <Button
                  class="mb-2"
                  v-for="provider in oAuthProviders.data"
                  :key="provider.name"
                  :loading="oAuth.loading"
                  :link="provider.auth_url"
                >
                  <div class="flex items-center">
                    <div v-html="provider.icon"></div>
                    <span class="ml-2"
                      >Continue with {{ provider.provider_name }}</span
                    >
                  </div>
                </Button>
              </template>
            </form>

            <div class="mt-6 text-center" v-if="!domainTeams.length">
              <router-link
                class="text-center text-base font-medium text-gray-900 hover:text-gray-700"
                :to="{
                  name: isLogin ? 'Signup' : 'Login',
                  query: { ...$route.query, forgot: undefined },
                }"
              >
                {{
                  isLogin
                    ? "New member? Create a new account."
                    : "Already have an account? Log in."
                }}
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { createResource, ErrorMessage, FormControl, Link } from "frappe-ui"
import { ref, onMounted, computed, watch } from "vue"
import FrappeDriveLogo from "../components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { useRoute } from "vue-router"
const route = useRoute()

const params = new URLSearchParams(new URL(window.location.href).search)
const email = ref(params.get("e") || "")
const first_name = ref("")
const last_name = ref("")
const team_name = ref(null)

const terms_accepted = ref(false)

const otpRequested = ref(false)
const otpValidated = ref(false)
const domainTeams = ref([])
const otp = ref("")
const otpResendCountdown = ref(0)
const account_request = ref(params.get("r") || "")
const isLogin = computed(() => route.name === "Login")

onMounted(() => {
  setInterval(() => {
    if (otpResendCountdown.value > 0) otpResendCountdown.value -= 1
  }, 1000)
})

const getReferrerIfAny = () => {
  const params = location.search
  const searchParams = new URLSearchParams(params)
  return searchParams.get("referrer")
}

const signup = createResource({
  url: "drive.api.product.signup",
  makeParams: () => ({
    account_request: account_request.value,
    first_name: first_name.value,
    last_name: last_name.value,
    referrer: getReferrerIfAny(),
  }),
  validate() {
    if (!terms_accepted.value) {
      throw new Error("Please accept the terms of service")
    }
  },
  onSuccess(data) {
    otpValidated.value = true
    if (data.location) window.location.replace(data.location)
    if ((data.message || data)?.length) domainTeams.value = data.message || data
    else domainTeams.value = [{ name: null, title: null }]
  },
  onError(err) {
    if (err.exc_type === "DuplicateEntryError") {
      toast("Account already exists - please login.")
    } else {
      toast("Failed to create account")
    }
  },
})

const oAuthProviders = createResource({
  url: "drive.api.product.oauth_providers",
  auto: true,
})

const oAuth = createResource({
  url: "drive.api.product.google_login",
  onSuccess(url) {
    window.location.href = url
  },
})

const sendOTP = createResource({
  url: "drive.api.product.send_otp",
  onSuccess(data) {
    otpRequested.value = true
    otpResendCountdown.value = 30
    account_request.value = data.message || data
    toast("Verification code sent to your email")
  },
  onError(err) {
    console.log(err)
    toast("Failed to send verification code")
  },
})
const verifyOTP = createResource({
  url: "drive.api.product.verify_otp",
  onSuccess: (data) => {
    otpValidated.value = true
    if (data.location) {
      window.location.replace(data.location)
    }
  },
})

const createPersonalTeam = createResource({
  url: "drive.api.product.create_personal_team",
  onSuccess: (data) => {
    if (data) window.location.replace("/t/" + data)
    window.reload()
  },
})

const requestInvite = createResource({
  url: "drive.api.product.request_invite",
})
</script>
