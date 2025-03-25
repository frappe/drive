<template>
  <div class="relative h-full">
    <div class="relative z-10 mx-auto pt-8 sm:w-max sm:pt-32">
      <!-- logo -->
      <div
        class="flex flex-col items-center"
        @dblclick="redirectForFrappeioAuth"
      >
        <img
          v-if="logo"
          class="inline-block h-12 w-12 rounded-md"
          :src="logo"
        />
        <FCLogo v-else class="inline-block h-12 w-12" />
      </div>
      <!-- card -->
      <div
        class="mx-auto w-full bg-white px-4 py-8 sm:mt-6 sm:w-112 sm:rounded-2xl sm:px-6 sm:py-6 sm:shadow-2xl"
      >
        <!-- title -->
        <div class="mb-7.5 text-center">
          <p class="mb-2 text-2xl font-semibold leading-6 text-gray-900">
            {{ title }}
          </p>
          <p
            class="break-words text-base font-normal leading-[21px] text-gray-700"
            v-if="subtitle"
          >
            <template
              v-if="typeof subtitle === 'object'"
              v-for="line in subtitle"
            >
              {{ line }}<br />
            </template>
            <template v-else>{{ subtitle }}</template>
          </p>
        </div>
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
import FCLogo from "@/components/EspressoIcons/MyDrive.vue"
import { toast } from "@/utils/toasts"

export default {
  name: "SaaSLoginBox",
  props: ["title", "subtitle", "logo"],
  components: {
    FCLogo,
  },
  mounted() {
    const params = new URLSearchParams(window.location.search)

    if (params.get("showRemoteLoginError")) {
      toast({
        title: "Token Invalid or Expired",
        color: "red",
        icon: "x",
      })
    }
  },
  methods: {
    redirectForFrappeioAuth() {
      window.location = "/f-login"
    },
  },
}
</script>
