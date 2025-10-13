<template>
  <div class="flex gap-1 text-ink-gray-8">
    <div
      class="rounded-full relative flex items-center justify-center p-0.5"
      :class="[colorClasses, props.size === 'sm' ? 'size-4.5' : 'size-6']"
    >
      <component
        :is="logo"
        :class="size == 'sm' ? 'h-[90%] w-[90%]' : 'h-[70%] w-[70%]'"
      />
    </div>
    <div
      v-if="showText"
      class="self-center"
    >
      {{ accessType[0].toUpperCase() + accessType.slice(1) }}
    </div>
  </div>
</template>
<script setup>

const props = defineProps({
  accessType: String,
  size: {
    type: String,
    default: "md",
  },
  showText: {
    type: Boolean,
    default: false,
  },
})

const logo = {
  team: LucideBuilding,
  public: LucideGlobe2,
  restricted: LucideLock,
}[props.accessType]

const colorClasses = {
  team: "bg-surface-blue-2 text-ink-blue-2",
  public: "bg-surface-red-2 text-ink-red-3",
  restricted: "text-ink-gray-7 bg-surface-gray-4",
}[props.accessType]
</script>
