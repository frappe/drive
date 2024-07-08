<template>
  <div
    ondragstart="return false;"
    ondrop="return false;"
    class="flex gap-x-3 flex-wrap justify-end items-center w-full min-h-8 mb-6"
  >
    <div class="flex gap-3 w-full justify-start items-center">
      <div
        v-if="$route.name === 'Shared'"
        class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
      >
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            $store.state.shareView === 'with'
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="$store.commit('toggleShareView', 'with')"
        >
          Shared with You
        </Button>
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            $store.state.shareView === 'by'
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="$store.commit('toggleShareView', 'by')"
        >
          Shared by You
        </Button>
      </div>
      <Dropdown :options="filterItems" placement="left">
        <Button
          >Filter
          <template #prefix>
            <Filter />
          </template>
          <template #suffix>
            <ChevronDown />
          </template>
        </Button>
      </Dropdown>
      <div v-for="(item, index) in activeFilters" :key="index">
        <div class="flex items-center border rounded pl-2 py-1 h-7 text-base">
          {{ item }}
          <Button
            variant="minimal"
            @click="$store.state.activeFilters.splice(index, 1)"
          >
            <template #icon>
              <FeatherIcon class="h-3 w-3" name="x" />
            </template>
          </Button>
        </div>
      </div>
      <div class="ml-auto flex gap-x-1 items-center">
        <Dropdown
          v-if="columnHeaders"
          :options="orderByItems"
          placement="right"
          class="basis-auto"
        >
          <div class="flex items-center whitespace-nowrap">
            <Button
              class="text-sm h-7 border-r border-slate-200 rounded-r-none"
              @click.stop="toggleAscending"
            >
              <DownArrow
                :class="{ '[transform:rotateX(180deg)]': ascending }"
                class="h-3.5"
              />
            </Button>
            <Button class="text-sm h-7 rounded-l-none flex-1 md:block">
              {{ orderByLabel }}
            </Button>
          </div>
        </Dropdown>
        <div
          class="bg-gray-100 rounded-md space-x-0.5 h-7 px-0.5 py-1 flex items-center"
        >
          <Button
            variant="ghost"
            class="max-h-6 leading-none transition-colors focus:outline-none"
            :class="[
              $store.state.view === 'grid'
                ? 'bg-white shadow-sm hover:bg-white active:bg-white'
                : '',
            ]"
            @click="$store.commit('toggleView', 'grid')"
          >
            <ViewGrid />
          </Button>
          <Button
            variant="ghost"
            class="max-h-6 leading-none transition-colors focus:outline-none"
            :class="[
              $store.state.view === 'list'
                ? 'bg-white shadow-sm hover:bg-white active:bg-white'
                : '',
            ]"
            @click="$store.commit('toggleView', 'list')"
          >
            <ViewList />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { FeatherIcon, Button, Dropdown } from "frappe-ui"
import ViewGrid from "@/components/EspressoIcons/ViewGrid.vue"
import ViewList from "@/components/EspressoIcons/ViewList.vue"
import DownArrow from "./EspressoIcons/DownArrow.vue"
import Filter from "./EspressoIcons/Filter.vue"
import ChevronDown from "./EspressoIcons/ChevronDown.vue"
import Folder from "./MimeIcons/Folder.vue"
import Archive from "./MimeIcons/Archive.vue"
import Document from "./MimeIcons/Document.vue"
import Spreadsheet from "./MimeIcons/Spreadsheet.vue"
import Presentation from "./MimeIcons/Presentation.vue"
import Audio from "./MimeIcons/Audio.vue"
import Image from "./MimeIcons/Image.vue"
import Video from "./MimeIcons/Video.vue"
import PDF from "./MimeIcons/PDF.vue"
import Unknown from "./MimeIcons/Unknown.vue"

export default {
  name: "DriveToolBar",
  components: {
    Button,
    Dropdown,
    ViewList,
    ViewGrid,
    DownArrow,
    Filter,
    ChevronDown,
    FeatherIcon,
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
    activeFilters() {
      return this.$store.state.activeFilters
    },
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
        onClick: () => {
          this.$store.commit("setSortOrder", {
            field: header.field,
            label: header.label,
            ascending: this.ascending,
          })
        },
      }))
    },
    filterItems() {
      return [
        {
          label: "Folder",
          icon: Folder,
          onClick: () => {
            // toggle folders only
            this.$store.state.activeFilters.push("Folder")
          },
        },
        {
          label: "Image",
          icon: Image,
          onClick: () => {
            this.$store.state.activeFilters.push("Image")
          },
        },
        {
          label: "Audio",
          icon: Audio,
          onClick: () => {
            this.$store.state.activeFilters.push("Audio")
          },
        },
        {
          label: "Video",
          icon: Video,
          onClick: () => {
            this.$store.state.activeFilters.push("Video")
          },
        },
        {
          label: "PDF",
          icon: PDF,
          onClick: () => {
            this.$store.state.activeFilters.push("PDF")
          },
        },
        {
          label: "Document",
          icon: Document,
          onClick: () => {
            this.$store.state.activeFilters.push("Document")
          },
        },
        {
          label: "Spreadsheet",
          icon: Spreadsheet,
          onClick: () => {
            this.$store.state.activeFilters.push("Spreadsheet")
          },
        },
        {
          label: "Archive",
          icon: Archive,
          onClick: () => {
            this.$store.state.activeFilters.push("Archive")
          },
        },
        {
          label: "Presentation",
          icon: Presentation,
          onClick: () => {
            this.$store.state.activeFilters.push("Presentation")
          },
        },
        {
          label: "Unknown",
          icon: Unknown,
          onClick: () => {
            this.$store.state.activeFilters.push("Unknown")
          },
        },
      ].filter((item) => !this.activeFilters.includes(item.label))
    },
  },
  mounted() {
    for (let element of this.$el.getElementsByTagName("button")) {
      element.classList.remove("focus:ring-2", "focus:ring-offset-2")
    }
  },
  methods: {
    toggleAscending() {
      this.$store.commit("setSortOrder", {
        field: this.orderByField,
        label: this.orderByLabel,
        ascending: !this.ascending,
      })
    },
  },
}
</script>
./EspressoIcons/Sort.vue
