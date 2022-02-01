<template>
  <LoginBox title="Log in to your account">
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
      <Button
        class="mt-4"
        :disabled="state === 'requestStarted'"
        @click="login"
        type="primary"
      >
        Submit
      </Button>
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
      state: null,
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
        this.state = 'requestStarted'
        if (this.email && this.password) {
          let res = await this.$call('login', {
            usr: this.email,
            pwd: this.password,
          })
          if (res) {
            this.auth.isLoggedIn = true
            this.auth.user = res.full_name
            this.$router.push('/')
          }
        }
      } catch (error) {
        this.errorMessage = error.messages.join('\n')
      } finally {
        this.state = null
      }
    },
  },
}
</script>
