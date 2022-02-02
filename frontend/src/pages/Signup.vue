<template>
  <LoginBox
    v-if="!status_200"
    title="Create your account"
    :class="{ 'pointer-events-none': loading }"
  >
    <form class="flex flex-col" @submit.prevent="signup()">
      <Input
        class="mb-4"
        label="Name"
        type="text"
        placeholder="John Doe"
        autocomplete="name"
        v-model="full_name"
        required
      />
      <Input
        label="Email"
        type="email"
        placeholder="johndoe@mail.com"
        autocomplete="email"
        v-model="email"
        required
      />
      <ErrorMessage class="mt-4" :message="errorMessage" />
      <Button class="mt-4" type="primary" :loading="loading"> Submit </Button>
      <div class="mt-10 text-center border-t">
        <div class="transform -translate-y-1/2">
          <span class="px-2 text-xs leading-8 tracking-wider text-gray-800 bg-white">OR</span>
        </div>
      </div>
      <router-link class="text-base text-center" to="/login">
        Already have an account? Log in.
      </router-link>
    </form>
  </LoginBox>
  <div v-else class="p-5 sm:p-20">
    <div
      class="
        flex flex-col flex-1
        items-center
        p-10
        text-base
        bg-white
        rounded-lg
        mx-auto
        shadow-lg
        w-full
        sm:w-96
      "
    >
      <div class="w-8 h-8 p-1 rounded-full" :class="iconContainerClass">
        <FeatherIcon :name="icon" :class="iconClass" />
      </div>
      <h2 class="mt-4 text-lg font-medium text-gray-900">
        {{ response.title }}
      </h2>
      <p class="text-base text-center text-gray-700 mt-1.5">
        <span v-html="response.message" />
      </p>
    </div>
  </div>
</template>

<script>
import LoginBox from '@/components/LoginBox.vue'
import { Input, ErrorMessage, FeatherIcon } from 'frappe-ui'

export default {
  name: 'Signup',
  components: {
    LoginBox,
    Input,
    ErrorMessage,
    FeatherIcon,
  },
  data() {
    return {
      email: null,
      full_name: null,
      errorMessage: null,
      loading: false,
      status_200: false,
      response: {
        title: null,
        message: null,
      },
    }
  },
  computed: {
    iconClass() {
      return {
        red: 'text-red-500',
        green: 'text-green-500',
      }[this.response.color]
    },
    iconContainerClass() {
      return {
        red: 'bg-red-100',
        green: 'bg-green-100',
        yellow: 'bg-yellow-100',
        blue: 'bg-blue-100',
        gray: 'bg-gray-100',
      }[this.response.color]
    },
    icon() {
      return {
        red: 'x',
        green: 'check',
      }[this.response.color]
    },
  },
  methods: {
    async signup() {
      try {
        this.errorMessage = null
        this.loading = true
        if (this.email && this.full_name) {
          let res = await this.$call('frappe.core.doctype.user.user.sign_up', {
            full_name: this.full_name,
            email: this.email,
            redirect_to: '',
          })
          if (res) {
            let [code] = res
            if (code === 0) {
              this.errorMessage = 'This account already exists'
            } else if (code === 1) {
              this.status_200 = true
              this.response.color = 'green'
              this.response.title = 'Verification Email Sent'
              this.response.message = `We have sent an email to
                <span class="font-semibold">${this.email}</span>. Please check your email for verification.`
            } else {
              this.status_200 = true
              this.response.color = 'red'
              this.response.title = 'Verification Needed'
              this.response.message = `Verification email was not sent. Please ask your administrator to
                verify your sign-up`
            }
          }
        }
      } catch (error) {
        this.errorMessage = error.messages.join('\n')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
