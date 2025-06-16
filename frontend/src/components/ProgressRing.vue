<template>
  <svg
    :height="radius * 2"
    :width="radius * 2"
  >
    <circle
      class="fill-transparent stroke-current"
      :class="secondaryClass"
      :cx="radius"
      :cy="radius"
      :r="normalizedRadius"
      :stroke-width="stroke"
      :stroke-dasharray="circumference"
    />
    <circle
      class="fill-transparent stroke-current origin-center -rotate-90 transition-all"
      :class="primaryClass"
      :cx="radius"
      :cy="radius"
      :r="normalizedRadius"
      :stroke-width="stroke"
      :stroke-dasharray="circumference"
      :stroke-dashoffset="strokeDashoffset"
    />
  </svg>
</template>
<script>
export default {
  name: "ProgressRing",
  props: {
    progress: {
      type: Number,
      required: true,
    },
    radius: {
      type: Number,
      default: 24,
    },
    stroke: {
      type: Number,
      default: 4,
    },
    primaryClass: {
      type: String,
      default: "text-black",
    },
    secondaryClass: {
      type: String,
      default: "text-ink-gray-1",
    },
  },
  computed: {
    normalizedRadius() {
      return this.radius - this.stroke
    },
    circumference() {
      return this.normalizedRadius * 2 * Math.PI
    },
    strokeDashoffset() {
      return this.circumference - (this.progress / 100) * this.circumference
    },
  },
}
</script>
