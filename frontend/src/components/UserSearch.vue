<template>
  <Popover transition="default">
    <template #target="{ open: openUsers, close: closeUsers }">
      <Input
        v-model="searchQuery"
        type="text"
        class="w-full"
        placeholder="Search for users, email or group"
        @input="handleInput($event, openUsers, closeUsers)" />
    </template>
    <template #body-main="{ togglePopover: toggleUsers }">
      <div class="p-1">
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
              size="xl"
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
      const headers = {
        Accept: "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "X-Frappe-Site-Name": window.location.hostname,
      };
      const res = await fetch(
        `/api/method/drive.utils.users.get_users_with_drive_user_role_and_groups?txt=${txt}`,
        {
          method: "GET",
          headers,
        }
      );
      if (res.ok) {
        const temp_response = await res.json();
        const data = temp_response.message;
        this.searchResults = data.filter((x) => x.email !== this.userId);
      }
    },
  },
};
</script>
