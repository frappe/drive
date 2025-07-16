<template>
  <div class="flex p-5 pb-0 h-12">
    <div
      v-if="selections?.length"
      class="my-auto w-[40%] text-base text-ink-gray-8"
    >
      {{ selections.length }} item{{ selections.length === 1 ? "" : "s" }}
      selected
    </div>
    <div
      v-else-if="$route.name === 'Shared'"
      class="bg-surface-gray-2 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 mr-4 py-1"
    >
      <TabButtons
        v-model="shareView"
        :buttons="[
          {
            label: 'By',
            value: 'by',
            onClick: () => {
              store.commit('toggleShareView', 'by')
            },
            disabled: !getEntities.data?.length,
          },
          {
            label: 'With you',
            value: 'with',
            onClick: () => {
              store.commit('toggleShareView', 'with')
            },
            disabled: !getEntities.data?.length,
          },
        ]"
      />
    </div>
    <TextInput
      ref="search-input"
      v-model="search"
      :disabled="!getEntities.data?.length"
      :class="selections.length ? 'hidden' : 'block'"
      :placeholder="__('Search')"
      class="w-[30%]"
    >
      <template #prefix>
        <LucideSearch class="size-4" />
      </template>
    </TextInput>

    <div class="flex gap-2 ml-auto my-auto">
      <template v-if="selections && !selections.length">
        <div
          v-if="activeFilters.length"
          class="flex flex-wrap items-start justify-end gap-1 ml-3"
        >
          <div
            v-for="(item, index) in activeFilters"
            :key="index"
          >
            <div
              class="flex items-center border rounded pl-2 py-1 h-7 text-base"
            >
              <component :is="ICON_TYPES[item]" />
              <span class="text-sm ml-2">{{ item }}</span>
              <Button
                variant="minimal"
                @click="activeFilters.splice(index, 1)"
              >
                <template #icon>
                  <LucideX class="size-3" />
                </template>
              </Button>
            </div>
          </div>
          <div
            v-for="(item, index) in activeTags"
            :key="index"
          >
            <div
              class="flex items-center border rounded pl-2 py-1 h-7 text-base"
            >
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
                  <LucideX class="size-3" />
                </template>
              </Button>
            </div>
          </div>
        </div>
        <Dropdown
          :options="
            Object.keys(ICON_TYPES).map((k) => ({
              label: __(k),
              icon: ICON_TYPES[k],
              onClick: () => activeFilters.push(k),
            }))
          "
          placement="right"
        >
          <Tooltip text="Filter">
            <Button :disabled="!getEntities.data?.length">
              <template #icon>
                <LucideFilter class="size-4" />
              </template>
            </Button>
          </Tooltip>
        </Dropdown>
        <Dropdown
          v-if="$route.name !== 'Recents'"
          :options="orderByItems"
          placement="right"
          class="basis-auto"
        >
          <div class="flex items-center whitespace-nowrap">
            <Button
              class="text-sm h-7 border-r border-slate-200 rounded-r-none"
              :disabled="!getEntities.data?.length"
              @click.stop="toggleAscending"
            >
              <template #icon>
                <LucideArrowDownAz
                  v-if="sortOrder.ascending"
                  class="size-4"
                />
                <LucideArrowUpZa
                  v-else
                  class="size-4"
                />
              </template>
            </Button>

            <Button
              class="text-sm h-7 rounded-l-none flex-1 md:block"
              :disabled="!getEntities.data?.length"
            >
              {{ __(sortOrder.label) }}
            </Button>
          </div>
        </Dropdown>

        <TabButtons
          v-model="viewState"
          :buttons="[
            {
              icon: 'grid',
              value: 'grid',
              disabled: !getEntities.data?.length,
            },
            {
              icon: 'list',
              value: 'list',
              disabled: !getEntities.data?.length,
            },
          ]"
        />
      </template>
      <div
        v-else-if="actionItems"
        class="flex gap-3 ml-4 overflow-auto"
      >
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
            <Button
              variant="outline"
              size="md"
              @click.once="item.action(selections)"
            >
              <template #icon>
                <component
                  :is="item.icon"
                  class="size-4 text-ink-gray-6"
                  :class="[item.class, item.danger ? 'text-ink-red-3' : '']"
                />
              </template>
            </Button>
          </Tooltip>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import {
  Button,
  Tooltip,
  Dropdown,
  TextInput,
  TabButtons,
  Switch,
} from "frappe-ui"
import {
  ref,
  computed,
  watch,
  useTemplateRef,
  h,
  reactive,
  defineComponent,
} from "vue"
import { ICON_TYPES, MIME_LIST_MAP, sortEntities } from "@/utils/files"
import { useStore } from "vuex"
import { onKeyDown } from "@vueuse/core"
import LucideLayoutGrid from "~icons/lucide/layout-grid"
import LucideLayoutList from "~icons/lucide/layout-list"

const rows = defineModel(Array)
const props = defineProps({
  selections: Array,
  actionItems: Array,
  getEntities: Object,
})
const store = useStore()

const name = computed(
  () => props.getEntities.params?.entity_name || props.getEntities.params?.team
)
const sortOrder = reactive(
  store.state.sortOrder[name.value] || {
    label: "Modified",
    field: "modified",
    ascending: false,
  }
)
const activeFilters = ref([])
const activeTags = computed(() => store.state.activeTags)

const search = ref("")
const viewState = ref(store.state.view)
watch(viewState, (val) => store.commit("toggleView", val))
const shareView = ref(store.state.shareView)
const searchInput = useTemplateRef("search-input")
// Do this as the resource data is updated by a lagging `fetch`
watch(
  [sortOrder, () => props.getEntities.loading],
  ([val, loading]) => {
    if (!rows.value || loading) return
    sortEntities(rows.value, val)
    props.getEntities.setData(rows.value)
    store.commit("setCurrentFolder", {
      entities: rows.value.filter?.((k) => k.title[0] !== "."),
    })
    if (name.value) {
      store.state.sortOrder[name.value] = val
      store.commit("setSortOrder", store.state.sortOrder)
    }
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
    onClick: () => {
      sortOrder.field = header.field
      sortOrder.label = header.label
    },
  }))
})
const toggleAscending = () => {
  sortOrder.ascending = !sortOrder.ascending
}

const columnHeaders = [
  {
    label: __("Name"),
    field: "title",
  },
  {
    label: __("Owner"),
    field: "owner",
  },
  {
    label: __("Modified"),
    field: "modified",
  },
  {
    label: __("Size"),
    field: "file_size",
  },
  {
    label: __("Type"),
    field: "mime_type",
  },
  {
    divider: true,
  },
  {
    component: defineComponent({
      setup() {
        return () =>
          h(Switch, {
            label: "Smart sort",
            modelValue: sortOrder.smart,
            "onUpdate:modelValue": (val) => (sortOrder.smart = val),
          })
      },
    }),
  },
]
</script>
