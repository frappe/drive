<template>
  <div
    class="mb-4 min-h-8 py-2 flex gap-3 flex-wrap justify-between items-center w-full px-5 md:px-0"
  >
    <Breadcrumbs :breadcrumbLinks="breadcrumbs" />
    <div class="flex gap-3 basis-full lg:basis-auto">
      <Dropdown :items="actionItems" class="basis-5/12 lg:basis-auto">
        <template v-slot="{ toggleDropdown }">
          <Button
            class="text-sm h-8 w-full"
            @click="toggleDropdown()"
            iconRight="chevron-down"
            :loading="actionLoading"
          >
            Actions
          </Button>
        </template>
      </Dropdown>
      <Dropdown :items="orderByItems" right class="basis-5/12 lg:basis-auto">
        <template v-slot="{ toggleDropdown }">
          <div class="flex items-center whitespace-nowrap">
            <Button
              class="text-sm h-8 px-2 border-r border-slate-200 rounded-r-none"
              @click="toggleAscending"
            >
              <svg
                class="h-4 w-4 stroke-current inline-block"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  :d="
                    ascending
                      ? 'M1.75 3.25h9m-9 4h6m-6 4h4m8.5-3.5l-2-2-2 2m2 4v-6'
                      : 'M1.75 3.25h9m-9 4h6m-6 4h4m4.5-.5l2 2 2-2m-2 1v-6'
                  "
                  stroke-miterlimit="10"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                ></path>
              </svg>
            </Button>
            <Button
              class="text-sm h-8 rounded-l-none flex-1"
              @click="toggleDropdown()"
            >
              Sort by {{ orderByLabel.toLowerCase() }}
            </Button>
          </div>
        </template>
      </Dropdown>
      <Button
        class="h-8 w-8 md:w-auto basis-2/12 lg:basis-auto"
        type="primary"
        @click="$emit('uploadFile')"
      >
        <span class="hidden md:inline">Upload</span>
        <span class="md:hidden text-4xl font-light">+</span>
      </Button>
    </div>
  </div>
</template>

<script>
import { Button, Dropdown } from 'frappe-ui'
import Breadcrumbs from '@/components/Breadcrumbs.vue'

export default {
  name: 'DriveToolBar',
  components: {
    Button,
    Breadcrumbs,
    Dropdown,
  },
  props: {
    breadcrumbs: {
      type: Array,
      required: true,
    },
    actionItems: {
      type: Array,
      required: true,
    },
    columnHeaders: {
      type: Array,
      required: true,
    },
    actionLoading: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['uploadFile'],
  computed: {
    orderByField() {
      return this.$store.state.sortOrder.field
    },
    orderByLabel() {
      return this.$store.state.sortOrder.label
    },
    ascending() {
      return this.$store.state.sortOrder.ascending
    },
    orderByItems() {
      return this.columnHeaders.map((header) => ({
        ...header,
        action: () => {
          this.$store.commit('setSortOrder', {
            field: header.field,
            label: header.label,
            ascending: this.ascending,
          })
        },
      }))
    },
  },
  methods: {
    toggleAscending() {
      this.$store.commit('setSortOrder', {
        field: this.orderByField,
        label: this.orderByLabel,
        ascending: !this.ascending,
      })
    },
  },
  mounted() {
    for (let element of this.$el.getElementsByTagName('button')) {
      element.classList.remove('focus:ring-2', 'focus:ring-offset-2')
    }
  },
}
</script>
