<template>
  <Popover transition="default">
    <template #target="{ open: openUsers, close: closeUsers }">
      <Input
        v-model="searchQuery"
        type="text"
        class="w-full"
        :placeholder="placeHolderText"
        @input="handleInput($event, openUsers, closeUsers)" />
    </template>
    <template #body-main="{ togglePopover: toggleUsers }">
      <div class="p-1 max-h-44 overflow-y-auto">
        <div v-for="result in searchResults" :key="result.email">
          <div
            class="flex items-center hover:bg-gray-100 cursor-pointer rounded-md py-1.5 px-2"
            @click="
              () => {
                selectResult(result);
                toggleUsers();
              }
            ">
            <Avatar
              class="mr-4"
              size="lg"
              :image="result.user_image"
              :label="result.full_name || result.name" />
            <div>
              <div class="text-gray-900 text-[13px]">
                {{ result.full_name || result.name }}
              </div>
              <div class="text-xs text-gray-600">
                {{ result.email }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script>
import { Popover, Button, Input, Avatar } from "frappe-ui";

export default {
  name: "UserSearch",
  components: {
    Popover,
    Button,
    Input,
    Avatar,
  },
  props: {
    placeHolderText: {
      type: String,
      default: "Search for users or emails",
      required: false,
    },
    searchGroups: {
      type: Boolean,
      default: false,
      required: false,
    },
  },
  emits: ["submit"],
  data() {
    return {
      searchQuery: "",
      newUserAccess: "Can view",
      searchResults: [],
      showDropdown: false,
    };
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
  },
  methods: {
    async handleInput(event, open, close) {
      this.searchQuery = event;
      if (event.length > 0) await this.search(this.searchQuery);
      else this.searchResults = [];
      this.searchResults.length > 0 ? open() : close();
    },
    selectResult(value) {
      this.$emit("submit", value);
      this.searchQuery = "";
    },
    async search(txt) {
      await this.$resources.search.fetch({ txt: txt });
    },
  },
  resources: {
    search() {
      return {
        url: this.searchGroups
          ? "drive.utils.users.get_users_with_drive_user_role_and_groups"
          : "drive.utils.users.get_users_with_drive_user_role",
        auto: false,
        onSuccess(data) {
          this.searchResults = data.filter((x) => x.email !== this.userId);
        },
      };
    },
  },
};
</script>
