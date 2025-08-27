<template>
  <Button
    class="flex w-full cursor-pointer items-center !rounded-[8px] group !py-[10px] !border-none search-sidebar-item"
    :class="
      isActive 
        ? '!bg-[#d4e1f9] !text-[#0149C1] shadow-sm active_icon' 
        : '!text-[#404040] !bg-white !border-white hover:!bg-[#d4e1f9] hover:!text-[#0149C1]'
    "
    @click="handleClick"
  >
    <div class="flex w-full items-center justify-between">
      <div class="flex items-center justify-start">
        <Tooltip
          :text="label"
          placement="right"
          arrow-class="fill-gray-900"
          :disabled="!isCollapsed"
        >
          <slot name="icon">
            <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
              <component
                :is="icon"
                class="size-5"
                :class="isActive ? '!text-[#0149C1]' : 'theme-text-secondaryColor'"
              />
            </span>
          </slot>
        </Tooltip>
        <span
          class="flex-1 flex-shrink-0 text-[14px] duration-200 ease-in-out font-medium"
          :class="[
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100',
            isActive ? '!text-[#0149C1]' : 'theme-text-secondaryColor'
          ]"
          style="font-weight: 500 !important;"
          v-if="!isCollapsed"
        >
          {{ label }}
        </span>
      </div>
      <slot name="right" />
    </div>
  </Button>
</template>

<script setup>
import { Tooltip } from "frappe-ui"
import { Button } from "primevue"
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"

const route = useRoute()
const router = useRouter()
const store = useStore()

const props = defineProps({
  icon: {
    type: [Function, Object],
    default: null,
  },
  label: {
    type: String,
    default: "",
  },
  to: {
    type: [Object, String],
    default: "",
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

function handleClick() {
  router.push({ path: props.to })
}

const isActive = computed(() => {
  if (!props.to) return false
  
  const currentPath = route.path
  const targetPath = props.to
  
  if (currentPath === targetPath) return true
  
  const first = store.state.breadcrumbs?.[0]
  if (first && (first.label === props.label || first.name === props.label)) {
    return true
  }
  
  return false
})
</script>

<style scoped>

</style>