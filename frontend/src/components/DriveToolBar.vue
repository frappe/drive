<template>
  <div
    class="flex gap-x-3 flex-wrap justify-start items-center w-full px-2 my-3"
  >
    <div class="flex w-full justify-start items-center flex-wrap">
      <Breadcrumbs :items="$store.state.breadcrumbs" />

      <div
        v-if="$route.name === 'Shared'"
        class="ml-5 bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
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
          With you
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
          By you
        </Button>
      </div>
      <div class="flex flex-wrap items-start justify-end gap-1 ml-3">
        <div v-for="(item, index) in activeFilters" :key="index">
          <div class="flex items-center border rounded pl-2 py-1 h-7 text-base">
            <component :is="item.icon"></component>
            <span class="text-sm ml-2">{{ item.label }}</span>

            <Button
              variant="minimal"
              @click="
                item.title
                  ? activeTags.splice(index, 1)
                  : activeFilters.splice(index, 1)
              "
            >
              <template #icon>
                <FeatherIcon class="h-3 w-3" name="x" />
              </template>
            </Button>
          </div>
        </div>
        <div v-for="(item, index) in activeTags" :key="index">
          <div class="flex items-center border rounded pl-2 py-1 h-7 text-base">
            <svg
              v-if="item.color"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                r="4.5"
                cx="8"
                cy="8"
                :fill="item.color"
                :stroke="item.color"
                stroke-width="3"
              />
            </svg>
            <span class="text-sm ml-2">{{ item.title }}</span>

            <Button
              variant="minimal"
              @click="$store.state.activeTags.splice(index, 1)"
            >
              <template #icon>
                <FeatherIcon class="h-3 w-3" name="x" />
              </template>
            </Button>
          </div>
        </div>
      </div>

      <div class="ml-auto flex gap-x-3 items-center">
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
                :class="{ '[transform:rotateX(180deg)]': sortOrder.ascending }"
                class="h-3.5"
              />
            </Button>
            <Button class="text-sm h-7 rounded-l-none flex-1 md:block">
              {{ sortOrder.label }}
            </Button>
          </div>
        </Dropdown>
        <Dropdown :options="filterItems" placement="right">
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
        <div
          v-if="false"
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

        <div v-if="!$store.getters.isLoggedIn" class="ml-2">
          <Button variant="solid" @click="$router.push({ name: 'Login' })">
            Sign In
          </Button>
        </div>
        <template v-for="button of possibleButtons" :key="button.route">
          <Button
            v-if="$route.name === button.route"
            class="line-clamp-1 truncate w-full"
            :disabled="!button.entities.data.length"
            variant="subtle"
            :theme="button.theme || 'gray'"
            @click="emitter.emit('showCTADelete')"
          >
            <template #prefix>
              <FeatherIcon :name="button.icon" class="w-4" />
            </template>
            {{ button.label }}
          </Button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FeatherIcon, Button, Dropdown, Breadcrumbs } from "frappe-ui"
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
import { computed, onMounted, watch, ref } from "vue"
import { useStore } from "vuex"
import { getRecents, getFavourites, getTrash } from "@/resources/files"

const store = useStore()
const props = defineProps({
  columnHeaders: Array,
  getEntitities: Object,
})
const sortOrder = ref(store.state.sortOrder)
watch(sortOrder, (val) => store.commit("setSortOrder", val))
const activeFilters = ref(store.state.activeFilters)
watch(activeFilters.value, (val) => store.commit("setActiveFilters", val))

const activeTags = computed(() => store.state.activeTags)
const orderByItems = computed(() => {
  return props.columnHeaders.map((header) => ({
    ...header,
    onClick: () =>
      (sortOrder.value = {
        field: header.field,
        label: header.label,
        ascending: sortOrder.value?.ascending,
      }),
  }))
})
const TYPES = [
  {
    label: "Folder",
    icon: Folder,
  },
  {
    label: "Image",
    icon: Image,
  },
  {
    label: "Audio",
    icon: Audio,
  },
  {
    label: "Video",
    icon: Video,
  },
  {
    label: "PDF",
    icon: PDF,
  },
  {
    label: "Document",
    icon: Document,
  },
  {
    label: "Spreadsheet",
    icon: Spreadsheet,
  },
  {
    label: "Archive",
    icon: Archive,
  },
  {
    label: "Presentation",
    icon: Presentation,
  },
  {
    label: "Unknown",
    icon: Unknown,
  },
]
TYPES.forEach((t) => {
  t.onClick = () => activeFilters.value.push(t)
})
const filterItems = computed(() => {
  return TYPES.filter((item) => !activeFilters.value.includes(item.label))
})
onMounted(() => {
  for (let element of document.getElementsByTagName("button")) {
    element.classList.remove("focus:ring-2", "focus:ring-offset-2")
  }
})
const toggleAscending = () => {
  sortOrder.value = {
    field: sortOrder.value.field,
    label: sortOrder.value.label,
    ascending: !sortOrder.value.ascending,
  }
}

const possibleButtons = [
  { route: "Recents", label: "Clear", icon: "clock", entities: getRecents },
  {
    route: "Favourites",
    label: "Clear",
    icon: "star",
    entities: getFavourites,
  },
  {
    route: "Trash",
    label: "Empty Trash",
    icon: "trash",
    entities: getTrash,
    theme: "red",
  },
]
</script>
