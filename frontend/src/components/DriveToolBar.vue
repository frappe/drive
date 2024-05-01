<template>
  <div
    ondragstart="return false;"
    ondrop="return false;"
    class="py-2 min-h-8 flex gap-3 flex-wrap justify-end items-center w-full">
    <div class="flex gap-3 w-full justify-end">
      <div
        v-if="$route.name === 'Shared'"
        class="mr-auto bg-gray-100 rounded-[10px] p-0.5 space-x-0.5 h-8 flex">
        <Button
          variant="ghost"
          class="leading-none transition-colors focus:outline-none"
          :class="[$store.state.shareView === 'with' ? 'bg-white shadow' : '']"
          @click="$store.commit('toggleShareView', 'with')">
          Shared with You
        </Button>
        <Button
          variant="ghost"
          class="leading-none transition-colors focus:outline-none"
          :class="[$store.state.shareView === 'by' ? 'bg-white shadow' : '']"
          @click="$store.commit('toggleShareView', 'by')">
          Shared by You
        </Button>
      </div>
      <Dropdown
        v-if="columnHeaders"
        :options="orderByItems"
        placement="right"
        class="basis-5/12 basis-auto">
        <div class="flex items-center whitespace-nowrap">
          <Button
            class="text-sm h-8 px-2 border-r border-slate-200 rounded-r-none"
            @click.stop="toggleAscending">
            <ViewOrder :class="{ '[transform:rotateX(180deg)]': ascending }" />
          </Button>
          <Button class="text-sm h-8 rounded-l-none flex-1 hidden md:block">
            {{ orderByLabel }}
          </Button>
        </div>
      </Dropdown>
      <div class="bg-gray-100 rounded-md p-0.5 space-x-0.5 h-8 flex">
        <Button
          variant="ghost"
          class="leading-none transition-colors focus:outline-none"
          :class="[$store.state.view === 'grid' ? 'bg-white shadow' : '']"
          @click="$store.commit('toggleView', 'grid')">
          <ViewGrid />
        </Button>
        <Button
          variant="ghost"
          class="leading-none transition-colors focus:outline-none"
          :class="[$store.state.view === 'list' ? 'bg-white shadow' : '']"
          @click="$store.commit('toggleView', 'list')">
          <ViewList />
        </Button>
      </div>
    </div>
  </div>
</template>

<script>
import { Button, Dropdown } from "frappe-ui";
import ViewGrid from "@/components/EspressoIcons/ViewGrid.vue";
import ViewList from "@/components/EspressoIcons/ViewList.vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import ViewOrder from "./EspressoIcons/ViewOrder.vue";

export default {
  name: "DriveToolBar",
  components: {
    Button,
    Breadcrumbs,
    Dropdown,
    ViewList,
    ViewGrid,
    ViewOrder,
  },
  props: {
    breadcrumbs: {
      type: Array,
      default: null,
    },
    actionItems: {
      type: Array,
      default: null,
    },
    columnHeaders: {
      type: Array,
      default: null,
    },
    actionLoading: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    orderByField() {
      return this.$store.state.sortOrder.field;
    },
    orderByLabel() {
      return this.$store.state.sortOrder.label;
    },
    ascending() {
      return this.$store.state.sortOrder.ascending;
    },
    orderByItems() {
      return this.columnHeaders.map((header) => ({
        ...header,
        onClick: () => {
          this.$store.commit("setSortOrder", {
            field: header.field,
            label: header.label,
            ascending: this.ascending,
          });
        },
      }));
    },
  },
  mounted() {
    for (let element of this.$el.getElementsByTagName("button")) {
      element.classList.remove("focus:ring-2", "focus:ring-offset-2");
    }
  },
  methods: {
    toggleAscending() {
      this.$store.commit("setSortOrder", {
        field: this.orderByField,
        label: this.orderByLabel,
        ascending: !this.ascending,
      });
    },
  },
};
</script>
