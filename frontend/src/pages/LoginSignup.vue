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
                {{ isLogin ? "Log in to Drive" : "Create a new account" }}
              </p>
              <p
                class="break-words text-base font-normal leading-[21px] text-gray-700"
              >
                {{ !isLogin ? "5 GB free - forever." : "Welcome back!" }}
              </p>
            </div>
            <form class="flex flex-col">
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
                  maxlength="6"
                  v-model="otp"
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
                  {{ isLogin ? "Login" : "Sign up" }} - Verify
                </Button>
              </template>
            </form>

            <div class="mt-6 text-center">
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
import GoogleIconSolid from "@/components/EspressoIcons/Home.vue"
import { ref, onMounted, computed, watch } from "vue"
import FrappeDriveLogo from "../components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { useRoute } from "vue-router"
const route = useRoute()

const email = ref("")
const first_name = ref("")
const last_name = ref("")
const team_name = ref("")

const terms_accepted = ref(false)

const isGoogleOAuthEnabled = true
const otpRequested = ref(false)
const otpValidated = ref(false)
const otp = ref("")
const otpResendCountdown = ref(0)
const account_request = ref("")
const isLogin = computed(() => route.name === "Login")

onMounted(() => {
  setInterval(() => {
    if (otpResendCountdown.value > 0) otpResendCountdown.value -= 1
  }, 1000)
})
// saasProduct() {
//       return this.$resources.signupSettings.data?.product_trial
//     },
//     countries() {
//       return this.$resources.signupSettings.data?.countries || []
//     },
//     isGoogleOAuthEnabled() {
//       return true
//     },
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
    team: team_name.value,
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
  },
  onError(err) {
    if (err.exc_type === "DuplicateEntryError") {
      toast("Account already exists - please login.")
    } else {
      toast("Failed to create account")
    }
  },
})

const signupOAuth = createResource({
  url: "drive.api.product.login_google",
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
</script>
