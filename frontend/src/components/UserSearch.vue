<template>
  <Menu as="div" class="w-full">
    <input
      type="text"
      ref="searchInput"
      v-model="searchQuery"
      @focus="search(searchQuery) && (showDropdown = true)"
      @blur="showDropdown = false"
      @keydown.enter="submit(searchQuery)"
      placeholder="Add user"
      class="w-full form-input placeholder-gray-500"
    />
    <MenuItems
      static
      v-show="showDropdown && searchResults.length > 0"
      class="z-10 w-full max-h-64 overflow-y-auto mt-2 p-1 bg-white rounded-md shadow-lg focus:outline-none divide-y divide-gray-100 left-0 origin-top-left"
    >
      <MenuItem
        v-for="result in searchResults"
        :key="result.value"
        v-slot="{ active }"
      >
        <button
          :class="active ? 'bg-gray-100' : 'text-gray-900'"
          class="flex flex-col items-start w-full px-2 py-2 text-base"
          @mousedown="selectResult(result.value)"
        >
          <div>{{ result.value }}</div>
          <div class="text-xs text-gray-600">{{ result.description }}</div>
        </button>
      </MenuItem>
    </MenuItems>
  </Menu>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'

export default {
  name: 'UserSearch',
  components: {
    FeatherIcon,
    Menu,
    MenuButton,
    MenuItems,
    MenuItem,
  },
  props: {
    modelValue: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue', 'submit'],
  data() {
    return {
      searchResults: [],
      showDropdown: false,
    }
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    searchQuery: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        this.search(value)
      },
    },
  },
  methods: {
    selectResult(value) {
      this.searchQuery = value
      this.submit(value)
    },
    submit(value) {
      this.$emit('submit', value)
      this.$refs.searchInput.blur()
    },
    async search(txt) {
      const headers = {
        Accept: 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'X-Frappe-Site-Name': window.location.hostname,
      }
      const res = await fetch(
        `/api/method/frappe.desk.search.search_link?doctype=User&filters={"ignore_user_type":1}&txt=${txt}`,
        {
          method: 'GET',
          headers,
        }
      )
      if (res.ok) {
        const data = await res.json()
        this.searchResults = data.results.filter(x => x.value !== this.userId)
      }
    },
  },
}
</script>
