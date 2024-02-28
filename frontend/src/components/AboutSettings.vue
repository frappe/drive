<template>
  <div class="flex h-full w-full flex-col items-start rounded-lg text-center">
    <h1 class="font-semibold">About</h1>
    <span class="text-sm py-1 mb-8 text-gray-600">
      ✨ A
      <a class="underline" href="https://frappe.io">Frappeverse</a>
      <span>product</span>
    </span>
    <div class="flex flex-col items-center w-full my-4">
      <div class="flex flex-col items-center w-full">
        <img
          class="h-20 -ml-3"
          src="https://raw.githubusercontent.com/frappe/drive/main/.github/logo_light.svg" />
      </div>
      <span class="text-base text-gray-600">
        100% open source on
        <a
          class="text-base text-black underline"
          href="https://github.com/frappe/drive">
          Github
        </a>
      </span>
      <span class="text-base text-gray-600">
        Built using
        <a
          class="text-base text-black underline"
          href="https://frappeframework.com">
          Frappe Framework
        </a>
      </span>
    </div>
    <span class="text-sm pb-4 text-gray-600 mt-auto">
      © Frappe Technologies Pvt. Ltd. and contributors
    </span>
  </div>
</template>
<script>
import { Avatar, Button, Checkbox, Input, Switch } from "frappe-ui";
import FrappeDriveLogo from "./FrappeDriveLogo.vue";

export default {
  name: "AboutSettings",
  components: { Avatar, Button, Input, Checkbox, Switch, FrappeDriveLogo },
  data() {
    return {
      fullName: this.$store.state.user.fullName,
    };
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded;
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ");
    },
    /* fullName() {
      return this.$store.state.user.fullName;
    }, */
    imageURL() {
      return this.$store.state.user.imageURL;
    },
  },
};
</script>
