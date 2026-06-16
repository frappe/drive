<template>
  <div class="flex h-screen w-full overflow-hidden sm:bg-surface-sidebar">
    <div class="w-full overflow-auto">
      <div class="relative h-full">
        <div class="relative z-10 mx-auto pt-8 sm:w-max sm:pt-20">
          <div class="flex flex-col items-center">
            <FrappeDriveLogo class="inline-block h-12 w-12 rounded-md" />
          </div>
          <div
            class="mx-auto w-full bg-surface-base p-5 sm:mt-6 sm:w-96 sm:rounded-xl sm:p-6 sm:shadow-md"
          >
            <h1
              class="mb-5 text-center text-3xl-semibold text-ink-gray-9"
            >
              {{
                params.get("t")
                  ? "Join " + params.get("t")
                  : "Create an account"
              }}
            </h1>

            <form class="flex flex-col gap-4">
              <FormControl
                v-model="email"
                label="Email"
                type="email"
                placeholder="johndoe@mail.com"
                autocomplete="email"
                :disabled="otpRequested"
                required
              />

              <template v-if="otpValidated">
                <div class="flex gap-4">
                  <FormControl
                    v-model="first_name"
                    label="First Name"
                    type="text"
                    placeholder="Robin"
                    autocomplete="off"
                    required
                  />
                  <FormControl
                    v-model="last_name"
                    label="Last Name"
                    type="text"
                    placeholder="Hood"
                    autocomplete="off"
                  />
                </div>
                <FormControl
                  v-model="password"
                  label="Password"
                  type="password"
                  autocomplete="new-password"
                  required
                />
                <FormControl
                  v-model="confirm_password"
                  label="Confirm Password"
                  type="password"
                  autocomplete="new-password"
                  required
                />
                <label class="mt-2 flex items-center gap-2 text-sm text-ink-gray-7">
                  <FormControl v-model="terms_accepted" type="checkbox" />
                  <span>
                    I accept the
                    <a
                      class="text-ink-gray-9 underline"
                      href="https://frappecloud.com/policies"
                      target="_blank"
                    >Terms and Policies</a>
                  </span>
                </label>
                <ErrorMessage
                  v-if="signup.error"
                  class="text-center"
                  :message="signup.error"
                />
                <Button
                  class="w-full"
                  variant="solid"
                  :loading="signup.loading"
                  :disabled="
                    !first_name.length || !password.length || !terms_accepted
                  "
                  @click="signup.submit()"
                >
                  Sign up
                </Button>
              </template>

              <template v-else-if="otpRequested">
                <FormControl
                  v-model="otp"
                  label="Verification code"
                  type="text"
                  placeholder="123456"
                  :disabled="verifyOTP.loading"
                  maxlength="6"
                  required
                  @keyup="
                    (e) =>
                      e.target.value.length === 6 &&
                      verifyOTP.submit({ account_request, otp })
                  "
                />
                <ErrorMessage
                  v-if="verifyOTP.error"
                  class="text-center"
                  :message="verifyOTP.error"
                />
                <Button
                  class="w-full"
                  variant="solid"
                  :loading="verifyOTP.loading"
                  @click="verifyOTP.submit({ account_request, otp })"
                >
                  Verify
                </Button>
                <Button
                  class="w-full"
                  variant="outline"
                  :loading="sendOTP.loading"
                  :disabled="otpResendCountdown > 0"
                  @click="sendOTP.submit()"
                >
                  Resend verification code{{
                    otpResendCountdown > 0
                      ? ` in ${otpResendCountdown}s`
                      : ""
                  }}
                </Button>
              </template>

              <template v-else>
                <ErrorMessage
                  v-if="sendOTP.error"
                  class="text-center"
                  :message="sendOTP.error"
                />
                <Button
                  class="w-full"
                  variant="solid"
                  :loading="sendOTP.loading"
                  @click="sendOTP.submit({ email, login: false })"
                >
                  Join
                </Button>
              </template>
            </form>

            <p class="mt-4 text-center text-xs text-ink-gray-6">
              Already have an account?
              <a class="text-ink-gray-9 hover:underline" :href="loginUrl">Log in</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { createResource, ErrorMessage, FormControl } from "frappe-ui"
import { ref, onMounted, computed } from "vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { settings } from "@/resources/permissions"

const params = new URLSearchParams(new URL(window.location.href).search)
const email = ref(params.get("e") || "")
const first_name = ref("")
const last_name = ref("")
const password = ref("")
const confirm_password = ref("")
const terms_accepted = ref(false)

const otp = ref("")
const otpResendCountdown = ref(0)
const account_request = ref(params.get("r") || "")
const otpRequested = ref(account_request.value !== "")
const otpValidated = ref(account_request.value !== "")

const loginUrl = computed(
  () =>
    "/login?redirect-to=" +
    encodeURIComponent(params.get("redirect-to") || "/drive")
)

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
    password: password.value,
    referrer: getReferrerIfAny(),
  }),
  validate() {
    if (password.value !== confirm_password.value) {
      return "Passwords do not match"
    }
    if (!terms_accepted.value) {
      return "Please accept the terms of service"
    }
  },
  onSuccess() {
    window.location.replace(
      "/drive/setup?redirect-to=" + (params.get("redirect-to") || "/drive")
    )
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
})

const verifyOTP = createResource({
  url: "drive.api.product.verify_otp",
  onSuccess: () => {
    otpValidated.value = true
    settings.fetch()
  },
})
</script>
