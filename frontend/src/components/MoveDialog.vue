<template>
  <Dialog v-model="open" :options="{ title: dialogTitle, size: '2xl' }">
    <template #body-header>
      <div class="mb-2 flex items-center justify-between">
        <div class="flex items-center justify-between">
          <DialogTitle as="header">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ dialogTitle }}
            </h3>
          </DialogTitle>
        </div>
        <Button variant="ghost" @click="close">
          <template #icon>
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              class="text-ink-gray-9"
            >
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M12.8567 3.85355C13.052 3.65829 13.052 3.34171 12.8567 3.14645C12.6615 2.95118 12.3449 2.95118 12.1496 3.14645L8.00201 7.29405L3.85441 3.14645C3.65914 2.95118 3.34256 2.95118 3.1473 3.14645C2.95204 3.34171 2.95204 3.65829 3.1473 3.85355L7.29491 8.00116L3.14645 12.1496C2.95118 12.3449 2.95118 12.6615 3.14645 12.8567C3.34171 13.052 3.65829 13.052 3.85355 12.8567L8.00201 8.70827L12.1505 12.8567C12.3457 13.052 12.6623 13.052 12.8576 12.8567C13.0528 12.6615 13.0528 12.3449 12.8576 12.1496L8.70912 8.00116L12.8567 3.85355Z"
                fill="currentColor"
              />
            </svg>
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
      <!-- <Autocomplete
        class="mb-2"
        v-if="allFolders.data"
        v-model="folderSearch"
        placeholder="Search for a folder"
        :options="
          allFolders.data.filter((k) =>
            currentFolder === ''
              ? k.label !== 'Home'
              : k.value !== currentFolder
          )
        "
      ></Autocomplete> -->
      <Tabs as="div" v-model="tabIndex" :tabs="tabs">
        <template #tab-panel>
          <div class="py-1">
            <Tree
              v-for="k in tree.children"
              :key="tree.name"
              nodeKey="value"
              :node="k"
            >
              <template
                #node="{ node, hasChildren, isCollapsed, toggleCollapsed }"
              >
                <div
                  class="flex items-center cursor-pointer select-none gap-1 h-[28px]"
                  @click="openEntity(node)"
                >
                  <div ref="iconRef" @click="toggleCollapsed($event)">
                    <LucideChevronDown
                      v-if="hasChildren && !isCollapsed"
                      class="size-3.5"
                    />
                    <LucideChevronRight
                      v-else-if="hasChildren"
                      class="size-3.5"
                    />
                  </div>
                  <div
                    class="flex-grow group rounded-sm text-base truncate h-full flex items-center pl-1"
                    :class="
                      currentFolder === node.value
                        ? 'bg-gray-200'
                        : 'hover:bg-gray-100 '
                    "
                  >
                    <Folder class="mr-1" />
                    <div v-if="node.value === null" class="overflow-visible">
                      <Input
                        @click.stop
                        @key.enter="openEntity(node)"
                        type="text"
                        v-focus
                        inputClass=" !h-6"
                        v-model="node.label"
                      />
                    </div>
                    <span v-else>{{ node.label }}</span>
                    <Button
                      class="shrink hidden group-hover:block ml-auto"
                      @click.stop="
                        (e) => {
                          let obj = {
                            parent: node.value,
                            value: null,
                            label: 'New folder',
                          }
                          node.children.push(obj)
                          if (isCollapsed) toggleCollapsed(e)
                        }
                      "
                    >
                      <NewFolder />
                    </Button>
                  </div></div
              ></template>
            </Tree>
            <p v-if="!tree.children.length" class="text-base text-center pt-5">
              No folders yet.
            </p>
          </div>
        </template>
      </Tabs>
      <div class="flex items-center justify-between max-h-7 mb-4">
        <div class="flex flex-col">
          <div class="flex items-center my-auto justify-start">
            <p class="text-sm pr-1">Moving to:</p>
            <Dropdown
              v-if="dropDownItems.length"
              class="h-7"
              :options="dropDownItems"
            >
              <Button variant="ghost">
                <template #icon>
                  <svg
                    class="w-4 text-gray-600"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="19" cy="12" r="1" />
                    <circle cx="5" cy="12" r="1" />
                  </svg>
                </template>
              </Button>
            </Dropdown>
            <span v-if="dropDownItems.length" class="text-gray-600 mx-0.5">
              {{ "/" }}
            </span>
            <div v-for="(crumb, index) in lastTwoBreadCrumbs" :key="index">
              <span
                v-if="breadcrumbs.length > 1 && index > 0"
                class="text-gray-600 mx-0.5"
              >
                {{ "/" }}
              </span>
              <button
                class="text-base cursor-pointer"
                :class="
                  index === lastTwoBreadCrumbs.length - 1
                    ? 'text-gray-900 text-base font-medium p-1'
                    : 'text-gray-600 text-base rounded-[6px] hover:bg-gray-100 p-1'
                "
                @click="closeEntity(crumb.name)"
              >
                {{ crumb.title }}
              </button>
            </div>
          </div>
        </div>
        <Button
          variant="solid"
          class="ml-auto"
          size="sm"
          :loading="move.loading"
          @click="
            $emit('success'),
              move.submit({
                entity_names: entities.map((obj) => obj.name),
                new_parent: currentFolder,
                is_private: breadcrumbs[breadcrumbs.length - 1].is_private,
              })
          "
        >
          <template #prefix>
            <Move />
          </template>
          Move
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { watch, computed, h, ref, reactive } from "vue"

import {
  createResource,
  Dialog,
  Button,
  Tabs,
  Dropdown,
  Autocomplete,
  Tree,
  Input,
} from "frappe-ui"
import { move, allFolders } from "@/resources/files"
import Home from "./EspressoIcons/Home.vue"
import Team from "./EspressoIcons/Organization.vue"
import Move from "./EspressoIcons/Move.vue"
import Folder from "./EspressoIcons/Folder.vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { LucideChevronDown } from "lucide-vue-next"
import { DialogTitle } from "@headlessui/vue"

const route = useRoute()
const currentFolder = ref("")
const emit = defineEmits(["update:modelValue", "success"])
const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  entities: {
    type: Object,
    required: false,
    default: null,
  },
})

const homeMap = {}
const teamMap = {}
allFolders.data.forEach((item) => {
  ;(item.is_private ? homeMap : teamMap)[item.value] = {
    ...item,
    children: [],
  }
})

const homeRoot = reactive({
  name: "",
  label: "Home",
  children: [],
})
const teamRoot = reactive({ name: "", label: "Team", children: [] })

allFolders.data.forEach((item) => {
  let map = item.is_private ? homeMap : teamMap
  const node = map[item.value]
  if (map[item.parent]) {
    map[item.parent].children.push(node)
  } else {
    ;(item.is_private ? homeRoot : teamRoot).children.push(node)
  }
})

const store = useStore()
const in_home = store.state.breadcrumbs[0].name == "Home"
const tabIndex = ref(in_home ? 0 : 1)
const tree = computed(() => (tabIndex.value === 0 ? homeRoot : teamRoot))

const open = computed({
  get() {
    return props.modelValue === "m"
  },
  set(newValue) {
    emit("update:modelValue", newValue || "")
  },
})

const dialogTitle = computed(() => {
  if (props.entities.length > 1) {
    return `Moving ${props.entities.length} items`
  } else {
    return `Moving "${props.entities[0].title}"`
  }
})

const lastTwoBreadCrumbs = computed(() => {
  if (breadcrumbs.value.length > 3) {
    return breadcrumbs.value.slice(-3)
  }
  return breadcrumbs.value
})

const dropDownItems = computed(() => {
  let allExceptLastTwo = breadcrumbs.value.slice(0, -3)
  return allExceptLastTwo.map((item) => {
    return {
      ...item,
      icon: null,
      label: item.title,
      onClick: () => closeEntity(item.name),
    }
  })
})

const tabs = [
  {
    label: "Home",
    icon: h(Home, { class: "w-4 h-4" }),
  },
  {
    label: "Team",
    icon: h(Team, { class: "w-4 h-4" }),
  },
  // {
  //   label: "Favourites",
  //   icon: h(Star, { class: "w-4 h-4" }),
  // },
]

const breadcrumbs = ref([
  { name: "", title: in_home ? "Home" : "Team", is_private: in_home ? 1 : 0 },
])
const folderSearch = ref(null)

const folderPermissions = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  params: {
    entity_name: currentFolder.value,
  },
  onSuccess: (data) => {
    let first = [{ name: "", title: data.is_private ? "Home" : "Team" }]
    breadcrumbs.value = first.concat(data.breadcrumbs.slice(1))
  },
})

const folderContents = createResource({
  url: "drive.api.list.files",
  makeParams: (params) => ({
    team: route.params.team,
    is_active: 1,
    folders: 1,
    ...params,
  }),
})

watch(
  tabIndex,
  (newValue) => {
    switch (newValue) {
      case 0:
        breadcrumbs.value = [{ name: "", title: "Home", is_private: 1 }]
        folderContents.fetch({
          entity_name: "",
          personal: 1,
        })
        break
      case 1:
        breadcrumbs.value = [{ name: "", title: "Team", is_private: 0 }]
        folderContents.fetch({
          entity_name: "",
          personal: 0,
        })
        break
      case 2:
        folderContents.fetch({
          entity_name: "",
          favourites_only: true,
        })
        break
    }
  },
  { immediate: true }
)

const createdNode = ref(null)
const createFolder = createResource({
  url: "drive.api.files.create_folder",
  makeParams(params) {
    return {
      ...params,
      team: route.params.team,
    }
  },
  validate(params) {
    if (!params?.title) return false
  },
  onSuccess(data) {
    createdNode.value.value = data.name
    currentFolder.value = data.name
    allFolders.data.push(createdNode.value)
    folderPermissions.fetch({
      entity_name: data.name,
    })
    createdNode.value = null
  },
})

function openEntity(node) {
  if (!node.value) {
    createdNode.value = node
    createFolder.fetch({
      title: node.label,
      personal: tabIndex.value === 0,
      parent: node.parent,
    })
  } else {
    currentFolder.value = node.value
    folderPermissions.fetch({
      entity_name: currentFolder.value,
    })
  }

  folderSearch.value = null
}

const toggleCollapsed = (obj, name) => {
  if (obj.name === name) {
    obj.isCollapsed = false
    return obj
  }
  for (let k of obj.children) {
    let res = toggleCollapsed(k, name)
    if (res) {
      obj.isCollapsed = false
      console.log(obj, res)
      return res
    }
  }
  return false
}

watch(folderSearch, (val) => {
  if (!folderSearch) return
  currentFolder.value = val.value
  // toggleCollapsed(tree.value, val.value)
})

function closeEntity(name) {
  const index = breadcrumbs.value.findIndex((obj) => obj.name === name)
  if (breadcrumbs.value.length > 1 && index !== breadcrumbs.value.length - 1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
    currentFolder.value = breadcrumbs.value[breadcrumbs.value.length - 1].name
    folderContents.fetch({
      entity_name: currentFolder.value,
      personal: currentFolder.value === "" ? 1 : -1,
    })
  }
}
</script>
