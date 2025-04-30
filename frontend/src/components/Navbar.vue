<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white border-b w-full px-4 py-2.5 h-12 flex items-center justify-between"
  >
    <div class="flex">
      <div v-if="selections?.length" class="flex flex-col">
        <div class="font text-md">
          <span class="font-semibold">{{ selections.length }}</span> item{{
            selections.length === 1 ? "" : "s"
          }}
          selected
        </div>
      </div>
      <Breadcrumbs
        v-else
        :items="store.state.breadcrumbs"
        :class="'select-none'"
      >
        <template #prefix="{ item }">
          <LoadingIndicator v-if="item.loading" scale="70" />
        </template>
      </Breadcrumbs>
      <div
        v-if="$route.name === 'Shared'"
        class="ml-5 bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
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
      <div
        v-if="activeFilters.length"
        class="flex flex-wrap items-start justify-end gap-1 ml-3"
      >
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
              @click="store.state.activeTags.splice(index, 1)"
            >
              <template #icon>
                <FeatherIcon class="h-3 w-3" name="x" />
              </template>
            </Button>
          </div>
        </div>
      </div>
    </div>
    <div class="flex gap-2">
      <template v-if="selections && !selections.length">
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
        <Dropdown :options="filterItems" placement="right">
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

        <div v-if="!store.getters.isLoggedIn" class="ml-2">
          <Button variant="solid" @click="$router.push({ name: 'Login' })">
            Sign In
          </Button>
        </div>

        <template v-for="button of possibleButtons" :key="button.route">
          <Button
            v-if="$route.name === button.route"
            class="line-clamp-1 truncate w-full"
            :disabled="!button.entities.data?.length"
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
        <Dropdown
          v-if="['Folder', 'Home', 'Team'].includes($route.name)"
          :options="newEntityOptions"
          placement="left"
          class="basis-5/12 lg:basis-auto"
        >
          <Tooltip text="Add or upload">
            <Button variant="solid">
              <div class="flex">
                <FeatherIcon name="plus" class="w-4 h-4" />
              </div>
            </Button>
          </Tooltip>
        </Dropdown>
      </template>
      <div v-else class="flex gap-3 ml-4 overflow-scroll">
        <template
          v-if="actionItems"
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
      <div
        v-if="connectedUsers.length > 1 && isLoggedIn"
        class="hidden sm:flex bg-gray-200 rounded justify-center items-center px-1"
      >
        <UsersBar />
      </div>

      <div v-if="!isLoggedIn" class="ml-auto">
        <Button variant="solid" @click="$router.push({ name: 'Login' })">
          Sign In
        </Button>
      </div>
    </div>
  </nav>
  <Dialogs :selections="activeEls" />
</template>
<script setup>
import UsersBar from "./UsersBar.vue"
import Dialogs from "./Dialogs.vue"
import {
  Button,
  Breadcrumbs,
  LoadingIndicator,
  FeatherIcon,
  Dropdown,
} from "frappe-ui"
import { ICON_TYPES } from "@/utils/files"
import Share from "./EspressoIcons/Share.vue"
import { useStore } from "vuex"
import ViewGrid from "@/components/EspressoIcons/ViewGrid.vue"
import ViewList from "@/components/EspressoIcons/ViewList.vue"
import DownArrow from "./EspressoIcons/DownArrow.vue"
import Filter from "./EspressoIcons/Filter.vue"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import Link from "./EspressoIcons/Link.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import NewFile from "./EspressoIcons/NewFile.vue"
import emitter from "@/emitter"
import { computed, watch, ref } from "vue"
import {
  getRecents,
  getFavourites,
  getTrash,
  createDocument,
} from "@/resources/files"
import { useRoute, useRouter } from "vue-router"
import Tooltip from "frappe-ui/src/components/Tooltip/Tooltip.vue"

const store = useStore()
const route = useRoute()
const router = useRouter()

const activeFilters = ref(store.state.activeFilters)
const sortOrder = ref(store.state.sortOrder)

const isLoggedIn = computed(() => store.getters.isLoggedIn)
const connectedUsers = computed(() => store.state.connectedUsers)
const activeTags = computed(() => store.state.activeTags)
const activeEls = computed(() => {
  return [store.state.activeEntity]
})
const filterItems = computed(() => {
  return ICON_TYPES.filter((item) => !activeFilters.value.includes(item.label))
})

const props = defineProps({
  selections: Array,
  actionItems: Array,
  columnHeaders: Array,
})

watch(sortOrder, (val) => store.commit("setSortOrder", val))
watch(activeFilters.value, (val) => store.commit("setActiveFilters", val))
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
ICON_TYPES.forEach((t) => {
  t.onClick = () => activeFilters.value.push(t)
})

// onMounted(() => {
//   for (let element of document.getElementsByTagName("button")) {
//     element.classList.remove("focus:ring-2", "focus:ring-offset-2")
//   }
// })

// Functions
const toggleAscending = () => {
  sortOrder.value = {
    ...sortOrder.value,
    ascending: !sortOrder.value.ascending,
  }
}

const newDocument = async () => {
  let data = await createDocument.submit({
    title: "Untitled Document",
    team: route.params.team,
    personal: store.state.breadcrumbs[0].label === "Home" ? 1 : 0,
    content: null,
    parent: store.state.currentFolder.name,
  })
  window.open(
    router.resolve({
      name: "Document",
      params: { team: route.params.team, entityName: data.name },
    }).href
  )
}

// Constants
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
    label: "Empty",
    icon: "trash",
    entities: getTrash,
    theme: "red",
  },
]

const newEntityOptions = [
  {
    group: "Upload",
    items: [
      {
        label: "Upload File",
        icon: FileUpload,
        onClick: () => emitter.emit("uploadFile"),
      },
      {
        label: "Upload Folder",
        icon: FolderUpload,
        onClick: () => emitter.emit("uploadFolder"),
      },
    ],
  },
  {
    group: "New...",
    items: [
      {
        label: "Document",
        icon: NewFile,
        onClick: newDocument,
      },
      {
        label: "Folder",
        icon: NewFolder,
        onClick: () => emitter.emit("newFolder"),
      },

      {
        label: "New Link",
        icon: Link,
        onClick: () => emitter.emit("newLink"),
      },
    ],
  },
]
</script>
