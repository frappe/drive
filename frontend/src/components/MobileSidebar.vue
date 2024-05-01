<template>
  <div v-if="open" class="fixed inset-0 z-20 flex md:hidden">
    <div class="flex w-auto flex-col bg-white">
      <!--       <div class="flex h-16 items-center border-b p-4">
        <FrappeDriveLogo />
      </div> -->
      <div class="grow p-4">
        <Sidebar @toggle-mobile-sidebar="open = !open" />
      </div>
    </div>
    <div class="grow bg-black opacity-25" @click="open = !open"></div>
  </div>
</template>

<script>
import Sidebar from "@/components/Sidebar.vue"

export default {
  name: "MobileSidebar",
  components: {
    Sidebar,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  computed: {
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
      },
    },
  },
}
</script>
