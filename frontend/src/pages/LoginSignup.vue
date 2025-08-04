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
                    ? "Đăng nhập Drive"
                    : params.get("t")
                    ? "Tham gia " + params.get("t")
                    : "Tạo tài khoản mới"
                }}
              </p>
              <p
                class="break-words text-base font-normal leading-[21px] text-ink-gray-7"
              >
                {{
                  !isLogin
                    ? params.get("t")
                      ? "Được cung cấp bởi nextGRP Drive."
                      : "Nhận 5 GB miễn phí, không cần thẻ tín dụng."
                    : "Chào mừng bạn trở lại!"
                }}
              </p>
            </div>

            <form class="flex flex-col">
              <FormControl
                v-model="email"
                label="Email"
                type="email"
                placeholder="tuanbd@mail.com"
                autocomplete="email"
                required
              />
              <FormControl
                v-model="password"
                label="Mật khẩu"
                type="password"
                placeholder="Nhập mật khẩu"
                autocomplete="current-password"
                class="mt-4"
                required
              />
              <template v-if="!isLogin">
                <div class="mt-5 flex flex-row gap-5">
                  <FormControl
                    v-model="first_name"
                    label="First Name"
                    type="text"
                    placeholder="Tuan"
                    variant="outline"
                    required
                  />
                  <FormControl
                    v-model="last_name"
                    label="Last Name"
                    type="text"
                    placeholder="Bui"
                    variant="outline"
                  />
                </div>
                <div class="!mt-6 flex gap-2">
                  <FormControl
                    v-model="terms_accepted"
                    type="checkbox"
                  />
                  <label class="text-base">
                    Tôi chấp nhận
                    <Link
                      class="!text-ink-gray-7"
                      to="https://frappecloud.com/policies"
                      target="_blank"
                    >
                      Điều khoản và Chính sách
                    </Link>
                  </label>
                </div>
              </template>

              <!-- Buttons -->
              <div class="mt-8 flex flex-col items-center gap-3">
                <Button
                  :loading="isLogin ? login.loading : signup.loading"
                  :disabled="!isLogin && (!first_name.length || !terms_accepted)"
                  variant="solid"
                  class="w-full font-medium"
                  @click="isLogin ? login.submit() : signup.submit()"
                >
                  {{ isLogin ? "Đăng nhập" : "Tạo tài khoản" }}
                </Button>

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
                      >{{ isLogin ? "Tiếp tục" : "Tham gia" }} với
                      {{ provider.provider_name }}</span
                    >
                  </div>
                </Button>
              </div>
            </form>

            <div v-if="!isLogin" class="mt-6 text-center">
              <router-link
                class="text-center text-base font-medium text-ink-gray-9 hover:text-ink-gray-7"
                :to="{
                  name: 'Login',
                  query: { ...$route.query, forgot: undefined },
                }"
              >
                Bạn đã có tài khoản? Đăng nhập.
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
import { ref, computed } from "vue"
import FrappeDriveLogo from "../components/FrappeDriveLogo.vue"
import { toast } from "@/utils/toasts"
import { useRoute, useRouter } from "vue-router"
import { settings } from "@/resources/permissions"

const route = useRoute()
const router = useRouter()
const params = new URLSearchParams(new URL(window.location.href).search)
const email = ref(params.get("e") || "")
const password = ref("")
const first_name = ref("")
const last_name = ref("")
const terms_accepted = ref(false)
const isLogin = computed(() => route.name === "Login")



const getReferrerIfAny = () => {
  const params = location.search
  const searchParams = new URLSearchParams(params)
  return searchParams.get("referrer")
}

const signup = createResource({
  url: "drive.api.product.direct_signup",
  makeParams: () => ({
    email: email.value,
    password: password.value,
    first_name: first_name.value,
    last_name: last_name.value,
    referrer: getReferrerIfAny(),
  }),
  validate() {
    if (!terms_accepted.value) {
      throw new Error("Vui lòng chấp nhận các điều khoản dịch vụ")
    }
    if (!email.value || !password.value || !first_name.value) {
      throw new Error("Vui lòng điền đầy đủ thông tin")
    }
  },
  onSuccess(data) {
    window.location.href = data.location || "/drive"
  },
  onError(err) {
    if (err.exc_type === "DuplicateEntryError") {
      toast("Tài khoản đã tồn tại - vui lòng đăng nhập.")
    } else {
      toast("Không tạo được tài khoản. Vui lòng thử lại sau.")
    }
  },
})

const login = createResource({
  url: "login",
  makeParams: () => ({
    usr: email.value,
    pwd: password.value,
  }),
  validate() {
    if (!email.value || !password.value) {
      throw new Error("Vui lòng nhập email và mật khẩu")
    }
  },
  onSuccess() {
    window.location.href = "/drive"
  },
  onError(err) {
    toast("Email hoặc mật khẩu không đúng")
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


</script>
