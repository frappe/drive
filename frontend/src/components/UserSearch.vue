<template>
  <div class="flex justify-between">
    <div class="flex bg-gray-100 rounded-lg">
      <Popover transition="default">
        <template #target="{ open: openUsers, close: closeUsers }">
          <div class="flex items-center justify-between h-[34px]">
            <Input
              v-model="searchQuery"
              type="text"
              placeholder="Add people or Email"
              class="h-7 focus:bg-inherit"
              @input="handleInput($event, openUsers, closeUsers)" />
            <Popover transition="default">
              <template #target="{ togglePopover: toggleAccess }">
                <Button
                  icon-right="chevron-down"
                  class="text-gray-900 text-[13px] rounded-lg h-7 w-full"
                  appearance="minimal"
                  @click="toggleAccess">
                  {{ newUserAccess }}
                </Button>
              </template>
              <template #body-main="{ togglePopover: toggleAccess }">
                <div class="p-1">
                  <div v-for="item in ['Can view', 'Can edit']" :key="item">
                    <div
                      class="text-gray-900 text-[13px] hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                      @click="
                        () => {
                          newUserAccess = item;
                          toggleAccess();
                        }
                      ">
                      {{ item }}
                    </div>
                  </div>
                </div>
              </template>
            </Popover>
          </div>
        </template>
        <template #body-main="{ togglePopover: toggleUsers }">
          <div class="p-1">
            <div v-for="result in searchResults" :key="result.value">
              <div
                class="hover:bg-gray-100 cursor-pointer rounded-md py-1.5 px-2"
                @click="
                  () => {
                    selectResult(result.value);
                    toggleUsers();
                  }
                ">
                <div class="text-gray-900 text-[13px]">
                  {{ result.value }}
                </div>
                <div class="text-xs text-gray-600">
                  {{ result.description }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </Popover>
    </div>
    <Button
      class="min-w-[75px] h-8 rounded-lg"
      appearance="primary"
      @click="selectResult(searchQuery)">
      Invite
    </Button>
  </div>
</template>

<script>
import { Popover, Button, Input } from "frappe-ui";

export default {
  name: "UserSearch",
  components: {
    Popover,
    Button,
    Input,
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
    writeAccess() {
      return this.newUserAccess === "Can view" ? 0 : 1;
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
      this.$emit("submit", { user: value, write: this.writeAccess });
      this.searchQuery = "";
    },
    async search(txt) {
      const headers = {
        Accept: "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "X-Frappe-Site-Name": window.location.hostname,
      };
      const res = await fetch(
        `/api/method/frappe.desk.search.search_link?doctype=User&filters={"ignore_user_type":1}&txt=${txt}`,
        {
          method: "GET",
          headers,
        }
      );
      if (res.ok) {
        const data = await res.json();
        this.searchResults = data.results.filter(
          (x) => x.value !== this.userId
        );
      }
    },
  },
};
</script>
