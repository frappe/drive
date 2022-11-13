<template>
  <div>
    <div class="flex mt-3.5 gap-2 ">
      <div class="bg-gray-100 rounded-lg w-full">
        <Popover transition="default">
          <template #target="{ togglePopover: toggleUsers }">
            <div class="flex items-center h-[34px] gap-2 w-full">
              <Input type="text" value="" placeholder="Add people or Email" class="h-7 focus:bg-inherit w-[266px]"
                v-model="searchQuery" @focus="search(searchQuery) && toggleUsers" />

              <Popover transition="default">
                <template #target="{ togglePopover: toggleAccess }">
                  <Button iconRight="chevron-down" @click="toggleAccess"
                    class="text-sm text-gray-900 text-[13px] rounded-lg h-7 hover:bg-inherit focus:bg-inherit active:bg-inherit"
                    appearance="minimal">
                    {{ newUserAccess }}
                  </Button>
                </template>
                <template #body-main="{ togglePopover: toggleAccess }">
                  <div class="p-1" @click="($event) => $event.stopPropagation()">
                    <div v-for="item in ['Can view', 'Can edit']" :key="item">
                      <div class="text-gray-900 text-[13px] hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2"
                        @click="() => {
                          newUserAccess = item
                          toggleAccess()
                        }">
                        {{ item }}
                      </div>
                    </div>
                  </div>
                </template>
              </Popover>

            </div>
          </template>
          <template #body-main="{ togglePopover: toggleUsers }">
            <div class="p-1" @click="($event) => $event.stopPropagation()">
              <div v-for="result in searchResults" :key="result.value">
                <div class="text-gray-900 text-[13px] hover:bg-gray-100 cursor-pointer rounded py-1.5 px-2" @click="() => {
                  toggleAccess()
                }">
                  {{ result }}
                </div>
              </div>
            </div>
          </template>
        </Popover>
      </div>
      <Button class="min-w-[75px] h-8 rounded-lg" appearance="primary" @click="$resources.share.fetch()">Invite</Button>
    </div>

    <!-- <Menu as="div" class="w-full">
      <input type="text" ref="searchInput" v-model="searchQuery" @focus="search(searchQuery) && (showDropdown = true)"
        @blur="showDropdown = false" @keydown.enter="submit(searchQuery)" placeholder="Add user"
        class="w-full form-input placeholder-gray-600 h-8 rounded-lg" />
      <MenuItems static v-show="showDropdown && searchResults.length > 0"
        class="z-10 w-full max-h-64 overflow-y-auto mt-2 p-1 bg-white rounded-md shadow-lg focus:outline-none divide-y divide-gray-100 left-0 origin-top-left">
        <MenuItem v-for="result in searchResults" :key="result.value" v-slot="{ active }">
        <button :class="active ? 'bg-gray-100' : 'text-gray-900'"
          class="flex flex-col items-start w-full px-2 py-2 text-base" @mousedown="selectResult(result.value)">
          <div>{{ result.value }}</div>
          <div class="text-xs text-gray-600">{{ result.description }}</div>
        </button>
        </MenuItem>
      </MenuItems>
    </Menu> -->
  </div>

</template>

<script>
import { Popover, Button, Input } from 'frappe-ui'

export default {
  name: 'UserSearch',
  components: {
    Popover,
    Button,
    Input
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
      newUserAccess: 'Can view',
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
