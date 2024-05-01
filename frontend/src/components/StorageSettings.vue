<template>
  <div class="flex h-full w-full flex-col items-start rounded-lg text-center">
    <h1 class="font-semibold">Storage</h1>
    <span class="text-sm py-1 mb-8 text-gray-600">
      Detailed information on currently available storage
    </span>
    <div class="flex flex-col items-center w-full my-4">
      <canvas
        id="chart-container"
        ref="canvasElement"
        style="width: 100%; height: 400px"
      ></canvas>
    </div>
  </div>
</template>
<script>
import { Avatar, Button, Checkbox, Input, Switch } from "frappe-ui"
import FrappeDriveLogo from "./FrappeDriveLogo.vue"

export default {
  name: "StorageSettings",
  components: { Avatar, Button, Input, Checkbox, Switch, FrappeDriveLogo },
  data() {
    return {
      fullName: this.$store.state.user.fullName,
      data: {
        labels: ["Category 1", "Category 2", "Category 3"],
        values: [25, 50, 75], // Percentage values
      },
    }
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ")
    },
    /* fullName() {
        return this.$store.state.user.fullName;
      }, */
    imageURL() {
      return this.$store.state.user.imageURL
    },
  },
  methods: {},
}
</script>
