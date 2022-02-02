<template>
  <LoginBox
    title="Log in to your account"
    :class="{ 'pointer-events-none': loading }"
  >
    <form class="flex flex-col" @submit.prevent="">
      <Input
        class="mb-4"
        label="Email"
        placeholder="johndoe@mail.com"
        v-model="email"
        name="email"
        autocomplete="email"
        :type="email !== 'Administrator' ? 'email' : 'text'"
        required
      />
      <Input
        label="Password"
        type="password"
        placeholder="•••••"
        v-model="password"
        name="password"
        autocomplete="current-password"
        required
      />
      <ErrorMessage :message="errorMessage" class="mt-4" />
      <Button class="mt-4" :loading="loading" @click="login" type="primary">
        Submit
      </Button>
      <div class="mt-10 text-center border-t">
        <div class="transform -translate-y-1/2">
          <span class="px-2 text-xs leading-8 tracking-wider text-gray-800 bg-white">OR</span>
        </div>
      </div>
      <router-link class="text-base text-center" to="/signup">
        Sign up for a new account
      </router-link>
    </form>
  </LoginBox>
</template>
<script>
import LoginBox from '@/components/LoginBox.vue'
import { Input, ErrorMessage } from 'frappe-ui'

export default {
  name: 'Login',
  props: {},
  components: {
    LoginBox,
    Input,
    ErrorMessage,
  },
  data() {
    return {
      loading: false,
      email: null,
      password: null,
      errorMessage: null,
      successMessage: null,
      redirect_route: null,
    }
  },
  methods: {
    async login() {
      try {
        this.errorMessage = null
        this.loading = true
        if (this.email && this.password) {
          let res = await this.$store.dispatch('login', {
            email: this.email,
            password: this.password,
          })
          if (res) {
            this.$router.push('/')
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
