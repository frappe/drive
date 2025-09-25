<template>
  <div class="flex p-5 pb-0 h-12">
    <div
      v-if="selections?.length"
      class="my-auto w-[40%] text-base text-ink-gray-8"
    >
      {{ selections.length }}
      {{ selections.length === 1 ? __("item") : __("items") }}
      {{ __("selected") }}
    </div>
    <div
      v-else-if="$route.name === 'Shared'"
      class="bg-surface-gray-2 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 mr-4 py-1"
    >
      <TabButtons
        v-model="shareView"
        :buttons="[
          {
            label: __('By'),
            value: 'by',
            onClick: () => {
              store.commit('toggleShareView', 'by')
            },
          },
          {
            label: __('With you'),
            value: 'with',
            onClick: () => {
              store.commit('toggleShareView', 'with')
            },
          },
        ]"
      />
    </div>
    <TextInput
      ref="search-input"
      v-model="search"
      :disabled
      :class="selections.length ? 'hidden' : 'block'"
      :placeholder="__('Search')"
      class="w-[30%]"
    >
      <template #prefix>
        <LucideSearch class="size-4" />
      </template>
    </TextInput>

    <div class="flex gap-2 ml-auto my-auto">
      <template v-if="!selections?.length">
        <div
          v-if="activeFilters.length"
          class="flex flex-wrap items-start justify-end gap-1 ml-3"
        >
          <div
            v-for="({ icon, name }, index) in activeFilters"
            :key="index"
          >
            <div
              class="flex items-center border rounded pl-2 py-1 h-7 text-base select-none"
            >
              <img :src="icon" />
              <span class="text-sm ml-2">{{ name }}</span>
              <Button
                variant="minimal"
                :icon="h(LucideX, { class: 'size-3' })"
                @click="activeFilters.splice(index, 1)"
              />
            </div>
          </div>
        </div>
        <Button
          v-if="getEntities.loading"
          :loading="true"
          label="Loading..."
        />
        <TeamSelector
          v-model="team"
          v-if="
            ['Shared', 'Recents', 'Favourites', 'Trash'].includes($route.name)
          "
          :none="true"
        />
        <Dropdown
          :options="
            availableFilterTypes.map(({ name, icon }) => ({
              label: __(name),
              icon: h('img', { src: icon }),
              onClick: () => activeFilters.push({ name, icon }),
              disabled: activeFilters.includes({ name, icon }),
            }))
          "
          :button="{
            icon: LucideFilter,
            tooltip: 'Filter',
          }"
          :disabled
          placement="right"
        />
        <Dropdown
          v-if="$route.name !== 'Recents'"
          :options="orderByItems"
          placement="right"
        >
          <div class="flex items-center whitespace-nowrap">
            <Button
              class="text-sm h-7 border-r border-slate-200 rounded-r-none"
              :disabled
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
              class="text-sm h-7 rounded-l-none flex-1"
              :disabled
            >
              <div class="flex items-center gap-2">
                {{ __(sortOrder.label) }}
                <template v-if="sortOrder.smart">
                  <LucideSparkles class="size-3" />
                </template>
              </div>
            </Button>
          </div>
        </Dropdown>

        <TabButtons
          v-model="viewState"
          :buttons="[
            {
              icon: 'grid',
              value: 'grid',
              disabled,
            },
            {
              icon: 'list',
              value: 'list',
              disabled,
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
          <Button
            variant="outline"
            :tooltip="item.label"
            size="md"
            @click.once="item.action(selections)"
          >
            <template #icon>
              <component
                :is="item.icon"
                class="size-4 text-ink-gray-6"
                :class="[item.class, item.theme ? 'text-ink-red-3' : '']"
              />
            </template>
          </Button>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { Button, Dropdown, TextInput, TabButtons, Switch } from "frappe-ui"
import { ref, computed, watch, useTemplateRef, h, defineComponent } from "vue"
import { MIME_LIST_MAP } from "@/utils/files"
import { getIconUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import { onKeyDown } from "@vueuse/core"
import LucideFilter from "~icons/lucide/filter"
import TeamSelector from "@/components/TeamSelector.vue"

import LucideX from "~icons/lucide/x"

const sortOrder = defineModel("sortOrder")
const search = defineModel("search")
const team = defineModel("team")
const props = defineProps({
  selections: Array,
  actionItems: Array,
  getEntities: Object,
})
const store = useStore()

const activeFilters = defineModel("filters")
const disabled = computed(() => !props.getEntities.data?.length)

const viewState = ref(store.state.view)
watch(viewState, (val) => store.commit("toggleView", val))
const shareView = ref(store.state.shareView)
const searchInput = useTemplateRef("search-input")

const availableFilterTypes = computed(() => {
  if (!props.getEntities.data) return []
  const types = new Set(props.getEntities.data.map((r) => r.file_type))
  if (props.getEntities.data.find((k) => k.is_group)) types.add("Folder")
  return Array.from(types)
    .sort((a, b) => (a > b ? 1 : -1))
    .map((t) => ({ name: t, icon: getIconUrl(t) }))
})

onKeyDown("Escape", () => {
  searchInput.value.el.blur()
  search.value = ""
})

const orderByItems = computed(() => {
  return columnHeaders.map((header) => ({
    ...header,
    onClick: () => {
      sortOrder.value.field = header.field
      sortOrder.value.label = header.label
    },
  }))
})
const toggleAscending = () => {
  sortOrder.value.ascending = !sortOrder.value.ascending
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
    group: true,
    hideLabel: true,
    items: [
      {
        component: defineComponent({
          setup() {
            return () =>
              h(Switch, {
                label: __("Smart"),
                disabled: sortOrder.value.field !== "title",
                modelValue: sortOrder.value.smart,
                "onUpdate:modelValue": (val) => (sortOrder.value.smart = val),
              })
          },
        }),
      },
    ],
  },
]
</script>
