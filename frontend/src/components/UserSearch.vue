<template>
  <div>
    <Menu as="div" class="w-full">
      <input
        ref="inputElement"
        type="text"
        v-model="searchQuery"
        @input="search(searchQuery)"
        @focus="
          () => {
            showDropdown = true
            search(searchQuery)
          }
        "
        @blur="showDropdown = false"
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
  </div>
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
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      showDropdown: false,
    }
  },
  methods: {
    selectResult(value) {
      let inputElement = this.$refs.inputElement
      inputElement.value = value
      inputElement.dispatchEvent(new Event('input'))
      this.showDropdown = false
    },
    onFocus() {},
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
        this.searchResults = data.results
      }
    },
  },
}
</script>
