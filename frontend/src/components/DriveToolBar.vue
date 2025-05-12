<template>
  <div class="flex px-4 pt-2">
    <div v-if="selections?.length" class="my-auto w-[40%]">
      {{ selections.length }} item{{ selections.length === 1 ? "" : "s" }}
      selected
    </div>
    <div
      v-if="$route.name === 'Shared'"
      class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
    >
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          store.state.shareView === 'with'
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="store.commit('toggleShareView', 'with')"
      >
        With you
      </Button>
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          store.state.shareView === 'by'
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="store.commit('toggleShareView', 'by')"
      >
        By you
      </Button>
    </div>
    <TextInput
      :class="selections.length ? 'hidden' : 'block'"
      ref="search-input"
      v-model="search"
      placeholder="Search"
      class="w-[30%]"
    >
      <template #prefix><LucideSearch class="w-4 h-4" /></template>
    </TextInput>
    <div
      v-if="activeFilters.length"
      class="flex flex-wrap items-start justify-end gap-1 ml-3"
    >
      <div v-for="(item, index) in activeFilters" :key="index">
        <div class="flex items-center border rounded pl-2 py-1 h-7 text-base">
          <component :is="ICON_TYPES[item]"></component>
          <span class="text-sm ml-2">{{ item }}</span>
          <Button variant="minimal" @click="activeFilters.splice(index, 1)">
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
            @click="store.state.activeTags.splice(index, 1)"
          >
            <template #icon>
              <FeatherIcon class="h-3 w-3" name="x" />
            </template>
          </Button>
        </div>
      </div>
    </div>
    <div class="flex gap-2 ml-auto">
      <template v-if="selections && !selections.length">
        <Dropdown
          v-if="$route.name !== 'Recents'"
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
                :class="{
                  '[transform:rotateX(180deg)]': sortOrder.ascending,
                }"
                class="h-3.5"
              />
            </Button>
            <Button class="text-sm h-7 rounded-l-none flex-1 md:block">
              {{ sortOrder.label }}
            </Button>
          </div>
        </Dropdown>
        <Dropdown
          :options="
            Object.keys(ICON_TYPES).map((k) => ({
              label: k,
              icon: ICON_TYPES[k],
              onClick: () => activeFilters.push(k),
            }))
          "
          placement="right"
        >
          <Tooltip text="Filter">
            <Button>
              <Filter />
            </Button>
          </Tooltip>
        </Dropdown>
        <div
          class="bg-gray-100 rounded-md space-x-0.5 h-7 px-0.5 py-1 flex items-center"
        >
          <Button
            variant="ghost"
            class="max-h-6 leading-none transition-colors focus:outline-none"
            :class="[
              store.state.view === 'grid'
                ? 'bg-white shadow-sm hover:bg-white active:bg-white'
                : '',
            ]"
            @click="store.commit('toggleView', 'grid')"
          >
            <ViewGrid />
          </Button>
          <Button
            variant="ghost"
            class="max-h-6 leading-none transition-colors focus:outline-none"
            :class="[
              store.state.view === 'list'
                ? 'bg-white shadow-sm hover:bg-white active:bg-white'
                : '',
            ]"
            @click="store.commit('toggleView', 'list')"
          >
            <ViewList />
          </Button>
        </div>
      </template>
      <div v-else-if="actionItems" class="flex gap-3 ml-4 overflow-scroll">
        <template
          v-for="item in actionItems
            .filter((i) => i.important && (selections.length === 1 || i.multi))
            .filter(
              (i) =>
                !i.isEnabled ||
                selections.every((e) => i.isEnabled(e, selections.length !== 1))
            )"
          :key="item.label"
        >
          <Tooltip :text="item.label">
            <Button variant="outline" @click.once="item.onClick(selections)">
              <div class="flex">
                <FeatherIcon
                  v-if="typeof item.icon === 'string'"
                  :name="item.icon"
                  class="w-4 h-4 text-gray-800"
                  :class="[item.class, item.danger ? 'text-red-500' : '']"
                />
                <component
                  :is="item.icon"
                  v-else
                  class="h-4 w-4 text-gray-800"
                  :class="[item.class, item.danger ? 'text-red-500' : '']"
                />
              </div>
            </Button>
          </Tooltip>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { Button, FeatherIcon, Tooltip, Dropdown, TextInput } from "frappe-ui"
import { ref, computed, watch, useTemplateRef } from "vue"
import { ICON_TYPES, MIME_LIST_MAP } from "@/utils/files"
import Share from "./EspressoIcons/Share.vue"
import { useStore } from "vuex"
import ViewGrid from "@/components/EspressoIcons/ViewGrid.vue"
import ViewList from "@/components/EspressoIcons/ViewList.vue"
import DownArrow from "./EspressoIcons/DownArrow.vue"
import Filter from "./EspressoIcons/Filter.vue"
import { onKeyDown } from "@vueuse/core"

const rows = defineModel(Array)
const props = defineProps({
  selections: Array,
  actionItems: Array,
  getEntities: Object,
})
const store = useStore()

const sortOrder = ref(store.state.sortOrder)
const activeFilters = ref([])
const activeTags = computed(() => store.state.activeTags)
const activeEls = computed(() => {
  return [store.state.activeEntity]
})

const search = ref("")
const searchInput = useTemplateRef("search-input")
// Do this as the resource data is updated by a lagging `fetch`
watch(
  [sortOrder, () => props.getEntities.loading],
  ([val, loading]) => {
    if (!rows.value || loading) return
    const field = val.field
    const order = val.ascending ? 1 : -1
    rows.value.sort((a, b) => {
      return a[field] == b[field] ? 0 : a[field] < b[field] ? order : -order
    })
    props.getEntities.setData(rows.value)
    store.commit("setCurrentFolder", {
      name: rows.value[0]?.parent_entity || "",
      entities: rows.value.filter?.((k) => k.title[0] !== "."),
    })
    store.commit("setSortOrder", val)
  },
  { immediate: true }
)

watch(activeFilters.value, (val) => {
  if (!val.length) {
    rows.value = props.getEntities.data
    return
  }
  const mime_types = []
  const isFolder = val.find((k) => k === "Folder")
  for (let k of val) {
    mime_types.push(...MIME_LIST_MAP[k])
  }
  rows.value = props.getEntities.data.filter(
    ({ mime_type, is_group }) =>
      mime_types.includes(mime_type) || (isFolder && is_group)
  )
})
watch(search, (val) => {
  const search = new RegExp(val, "i")
  rows.value = props.getEntities.data.filter((k) => search.test(k.title))
})

onKeyDown("Escape", () => {
  searchInput.value.el.blur()
  search.value = ""
})

const orderByItems = computed(() => {
  return columnHeaders.map((header) => ({
    ...header,
    onClick: () =>
      (sortOrder.value = {
        field: header.field,
        label: header.label,
        ascending: sortOrder.value?.ascending,
      }),
  }))
})
const toggleAscending = () => {
  sortOrder.value = {
    ...sortOrder.value,
    ascending: !sortOrder.value.ascending,
  }
}

const columnHeaders = [
  {
    label: "Name",
    field: "title",
  },
  {
    label: "Owner",
    field: "owner",
  },
  {
    label: "Modified",
    field: "modified",
  },
  {
    label: "Size",
    field: "file_size",
  },
  {
    label: "Type",
    field: "mime_type",
  },
]
</script>
