<template>
  <LoginBox
    title="Log in to your account"
    :class="{ 'pointer-events-none': loading }"
  >
    <form class="flex flex-col" @submit.prevent="">
      <Input
        v-model="email"
        class="mb-4"
        label="Email"
        placeholder="johndoe@mail.com"
        name="email"
        autocomplete="email"
        :type="email !== 'Administrator' ? 'email' : 'text'"
      />
      <Input
        v-model="password"
        label="Password"
        type="password"
        placeholder="••••••••"
        name="password"
        autocomplete="current-password"
      />
      <ErrorMessage :message="errorMessage" class="mt-4" />
      <Button
        class="mt-4 focus:ring-0 focus:ring-offset-0"
        :loading="loading"
        variant="solid"
        @click="login"
      >
        Submit
      </Button>
      <div class="mt-10 text-center border-t">
        <div class="transform -translate-y-1/2">
          <span
            class="px-2 text-xs leading-8 tracking-wider text-gray-800 bg-white"
          >
            OR
          </span>
        </div>
      </div>
      <Button
        v-for="provider in $resources.authProviders.data"
        :key="provider.name"
        class="mb-4 focus:ring-0 focus:ring-offset-0"
        variant="solid"
        @click="redirect(provider.auth_url)"
      >
        <template v-if="provider.name == 'frappe'" #prefix>
          <svg
            class="h-4.5"
            style="fill: white"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M5 3.68891V5.37783H11.5H18V3.68891V2H11.5H5V3.68891Z" />
            <path
              d="M5 15.9374V21.2443H7.07628H9.15256V17.6341V14.0238H13.1502H17.1478V12.3272V10.6305H11.0739H5V15.9374Z"
            />
          </svg>
        </template>
        Login via {{ provider.provider_name }}
      </Button>
      <router-link class="text-base text-center" to="/signup">
        Sign up for a new account
      </router-link>
    </form>
  </LoginBox>
</template>
<script>
import { Input, ErrorMessage } from "frappe-ui"
import LoginBox from "@/components/LoginBox.vue"

export default {
  name: "Login",
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
    redirect(link) {
      window.location.href = link
    },
    async login() {
      try {
        this.errorMessage = null
        this.loading = true
        if (this.email && this.password) {
          let res = await this.$store.dispatch("login", {
            email: this.email,
            password: this.password,
          })
          if (res) {
            this.$router.push("/home")
          }
        }
      } catch (error) {
        this.errorMessage = error.messages.join("\n")
      } finally {
        this.loading = false
      }
    },
  },
  resources: {
    authProviders() {
      return {
        url: "drive.api.api.oauth_providers",
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
        auto: true,
      }
    },
  },
}
</script>

<style>
html {
  -webkit-user-select: none;
  /* Safari */
  -ms-user-select: none;
  /* IE 10 and IE 11 */
  user-select: none;
  /* Standard syntax */
}
</style>
