<template>
  <div class="mb-4 min-h-8 py-2 flex gap-3 flex-wrap justify-between items-center w-full px-5 md:px-0">
    <Breadcrumbs v-if="breadcrumbs" :breadcrumbLinks="breadcrumbs" />
    <div class="flex gap-3 basis-full lg:basis-auto">
      <Dropdown v-if="actionItems" :options="actionItems" placement="left" class="basis-5/12 lg:basis-auto">
        <Button class="text-sm h-8 w-full" iconRight="chevron-down" :loading="actionLoading"
          :disabled="!actionItems.length > 0">
          Actions
        </Button>
      </Dropdown>
      <Dropdown v-if="columnHeaders" :options="orderByItems" placement="right" class="basis-5/12 lg:basis-auto">
        <div class="flex items-center whitespace-nowrap">
          <Button class="text-sm h-8 px-2 border-r border-slate-200 rounded-r-none" @click.stop="toggleAscending">
            <svg class="h-4 w-4 stroke-current inline-block" xmlns="http://www.w3.org/2000/svg">
              <path :d="
                ascending
                  ? 'M1.75 3.25h9m-9 4h6m-6 4h4m8.5-3.5l-2-2-2 2m2 4v-6'
                  : 'M1.75 3.25h9m-9 4h6m-6 4h4m4.5-.5l2 2 2-2m-2 1v-6'
              " stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </Button>
          <Button class="text-sm h-8 rounded-l-none flex-1">
            Sort by {{ orderByLabel.toLowerCase() }}
          </Button>
        </div>
      </Dropdown>
      <Button v-if="showViewButton" icon="info"></Button>
      <div class="bg-gray-100 rounded-md p-0.5 space-x-0.5">
        <Button icon="grid" @click="$store.commit('toggleView', 'grid')"
          :style="[$store.state.view === 'grid' && { 'background': '#FFF' }]"></Button>
        <Button icon="list" @click="$store.commit('toggleView', 'list')"
          :style="[$store.state.view === 'list' && { 'background': '#FFF' }]"></Button>
      </div>
      <Button v-if="showUploadButton" class="h-8 w-8 md:w-auto basis-2/12 lg:basis-auto" appearance="primary"
        @click="$emit('uploadFile')">
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
    },
    actionItems: {
      type: Array,
    },
    columnHeaders: {
      type: Array,
    },
    showUploadButton: {
      type: Boolean,
      default: true,
    },
    showViewButton: {
      type: Boolean,
      default: true,
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
        handler: () => {
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
