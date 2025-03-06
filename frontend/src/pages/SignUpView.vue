<template>
  <form class="flex flex-col space-y-4" @submit.prevent="submit">
    <FormControl
      v-model="email"
      label="Email"
      type="email"
      placeholder="johndoe@mail.com"
      autocomplete="email"
      :readonly="!!props.requestKey || isVerificationStep"
      required
    />
    <FormControl
      v-if="isVerificationStep"
      v-model="otp"
      label="Verification Code"
      type="text"
      placeholder="5 digit verification code"
      maxlength="5"
      autocomplete="email"
      required
    />
    <template v-if="props.requestKey">
      <FormControl
        v-model="firstName"
        label="First Name"
        type="text"
        placeholder="John"
        autocomplete="given-name"
        required
      />
      <FormControl
        v-model="lastName"
        label="Last Name"
        type="text"
        placeholder="Doe"
        autocomplete="family-name"
        required
      />
      <FormControl
        v-model="password"
        label="Password"
        type="password"
        placeholder="••••••••"
        name="password"
        autocomplete="current-password"
        required
      />
    </template>
    <ErrorMessage :message="errorMessage" />
    <Button
      variant="solid"
      :loading="signUp.loading || verifyOtp.loading || createAccount.loading"
    >
      {{ buttonLabel }}
    </Button>
    <Button
      v-if="isVerificationStep"
      type="button"
      :loading="resendOtp.loading"
      @click="resendOtp.submit()"
    >
      Resend OTP
    </Button>
  </form>
  <div class="mt-6 text-center">
    <router-link
      class="text-center text-base font-medium hover:underline"
      to="/login"
    >
      Already have an account? Log in.
    </router-link>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Button, ErrorMessage, FormControl, createResource } from "frappe-ui"

import { toast } from "@/utils/toasts"

const router = useRouter()
const { login } = { login: true }

const props = defineProps({
  requestKey: {
    type: String,
    required: false,
  },
})

const isVerificationStep = ref(false)
const email = ref("")
const otp = ref("")
const firstName = ref("")
const lastName = ref("")
const password = ref("")
const accountRequest = ref("")
const errorMessage = ref("")

const buttonLabel = computed(() => {
  if (props.requestKey) return "Create Account"
  return isVerificationStep.value ? "Verify" : "Sign Up"
})

const signUp = createResource({
  url: "mail.api.account.self_signup",
  makeParams() {
    return { email: email.value }
  },
  onSuccess(data) {
    errorMessage.value = ""
    accountRequest.value = data
    isVerificationStep.value = true
    raiseToast(
      "A verification code has been sent to your registered email address."
    )
  },
  onError(error) {
    errorMessage.value = error.messages[0]
  },
})

const resendOtp = createResource({
  url: "mail.api.account.resend_otp",
  makeParams() {
    return { account_request: accountRequest.value }
  },
  onSuccess() {
    raiseToast(
      "A verification code has been sent to your registered email address."
    )
  },
  onError(error) {
    raiseToast(error.messages[0], "error")
  },
})

const verifyOtp = createResource({
  url: "mail.api.account.verify_otp",
  makeParams() {
    return {
      account_request: accountRequest.value,
      otp: otp.value,
    }
  },
  onSuccess(requestKey) {
    errorMessage.value = ""
    router.push({ name: "AccountSetup", params: { requestKey } })
  },
  onError(error) {
    errorMessage.value = error.messages[0]
  },
})

const getAccountRequest = createResource({
  url: "mail.api.account.get_account_request",
  makeParams() {
    return { request_key: props.requestKey }
  },
  onSuccess(data) {
    if (
      (data?.email || data?.account) &&
      !data?.is_verified &&
      !data?.is_expired
    )
      email.value = data.account ? data.account : data.email
    else router.replace({ name: "SignUp" })
  },
})

const createAccount = createResource({
  url: "mail.api.account.create_account",
  makeParams() {
    return {
      request_key: props.requestKey,
      first_name: firstName.value,
      last_name: lastName.value,
      password: password.value,
    }
  },
  onSuccess() {
    errorMessage.value = ""
    login.submit({ usr: email.value, pwd: password.value })
  },
  onError(error) {
    errorMessage.value = error.messages[0]
  },
})

watch(
  () => props.requestKey,
  (val) => {
    isVerificationStep.value = false
    if (!val) return
    if (val.length === 32) getAccountRequest.submit()
    else router.replace({ name: "SignUp" })
  },
  { immediate: true }
)

const submit = () => {
  if (props.requestKey) createAccount.submit()
  else if (isVerificationStep.value) verifyOtp.submit()
  else signUp.submit()
}
</script>
