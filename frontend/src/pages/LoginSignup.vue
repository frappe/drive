<template>
  <div class="flex h-screen w-full overflow-hidden sm:bg-surface-menu-bar">
    <div class="w-full overflow-auto">
      <div class="relative h-full">
        <div class="relative z-10 mx-auto pt-8 sm:w-max sm:pt-20">
          <div class="flex flex-col items-center">
            <FrappeDriveLogo class="inline-block h-12 w-12 rounded-md" />
          </div>
          <div
            class="mx-auto w-full bg-surface-white px-4 py-8 sm:mt-6 sm:w-112 sm:rounded-2xl sm:px-6 sm:py-6 sm:shadow-2xl"
          >
            <div class="mb-7.5 text-center">
              <p class="mb-2 text-2xl font-semibold leading-6 text-ink-gray-9">
                {{
                  isLogin
                    ? "Login to Drive"
                    : params.get("t")
                    ? "Join " + params.get("t")
                    : "Create a new account"
                }}
              </p>
              <p
                class="break-words text-base font-normal leading-[21px] text-ink-gray-7"
              >
                {{
                  !isLogin
                    ? params.get("t")
                      ? "Powered by Frappe Drive."
                      : "Get 5 GB for free, no credit card required."
                    : "Welcome back!"
                }}
              </p>
            </div>

            <form class="flex flex-col">
              <FormControl
                v-model="email"
                label="Email"
                type="email"
                placeholder="johndoe@mail.com"
                autocomplete="email"
                :disabled="otpRequested"
                required
              />
              <template v-if="otpValidated && !isLogin">
                <div class="mt-5 flex flex-row gap-5">
                  <FormControl
                    v-model="first_name"
                    label="First Name"
                    type="text"
                    placeholder="Robin"
                    variant="outline"
                    required
                  />
                  <FormControl
                    v-model="last_name"
                    label="Last Name"
                    type="text"
                    placeholder="Hood"
                    variant="outline"
                  />
                </div>
                <div class="!mt-6 flex gap-2">
                  <FormControl
                    v-model="terms_accepted"
                    type="checkbox"
                  />
                  <label class="text-base">
                    I accept the
                    <Link
                      class="!text-ink-gray-7"
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
                    :loading="signup.loading"
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
                  v-model="otp"
                  label="Verification code"
                  type="text"
                  class="mt-4"
                  placeholder="123456"
                  :disabled="verifyOTP.loading"
                  maxlength="6"
                  required
                  @keyup="
                    (e) =>
                      e.target.value.length === 6 &&
                      verifyOTP.submit({
                        account_request,
                        otp,
                      })
                  "
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
                  :disabled="otpResendCountdown > 0"
                  @click="sendOTP.submit()"
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
                  @click="sendOTP.submit({ email, login: isLogin })"
                >
                  {{ isLogin ? "Login" : "Join" }}
                </Button>
                <div class="mt-6 border-t text-center">
                  <div class="-translate-y-1/2 transform">
                    <span
                      class="relative bg-surface-white px-2 text-sm font-medium leading-8 text-ink-gray-8"
                    >
                      or
                    </span>
                  </div>
                </div>
                <Button
                  v-for="provider in oAuthProviders.data"
                  :key="provider.name"
                  class="mb-2"
                  :loading="oAuth.loading"
                  :link="provider.auth_url"
                >
                  <div class="flex items-center">
                    <div v-html="provider.icon" />
                    <span class="ml-2"
                      >{{ isLogin ? "Continue" : "Join" }} with
                      {{ provider.provider_name }}</span
                    >
                  </div>
                </Button>
              </template>
            </form>

            <div class="mt-6 text-center">
              <router-link
                class="text-center text-base font-medium text-ink-gray-9 hover:text-ink-gray-7"
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
import { ref, onMounted, computed } from "vue"
import FrappeDriveLogo from "../components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { useRoute, useRouter } from "vue-router"
import { settings } from "@/resources/permissions"

const route = useRoute()
const router = useRouter()
const params = new URLSearchParams(new URL(window.location.href).search)
const email = ref(params.get("e") || "")
const first_name = ref("")
const last_name = ref("")
const terms_accepted = ref(false)

const otp = ref("")
const otpResendCountdown = ref(0)
const account_request = ref(params.get("r") || "")
const otpRequested = ref(account_request.value !== "")
const otpValidated = ref(account_request.value !== "")
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
    window.location.href = data.location
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
    if (JSON.stringify(err).includes("not found"))
      toast("Please sign up first!")
    else toast("Failed to send verification code")
  },
})

const verifyOTP = createResource({
  url: "drive.api.product.verify_otp",
  onSuccess: (data) => {
    otpValidated.value = true
    settings.fetch()
    if (data.location) {
      window.location.replace(data.location)
    }
  },
})
</script>
