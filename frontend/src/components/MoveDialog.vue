<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
    :options="{ size: 'lg' }"
  >
    <template #body-main>
      <div class="p-4 sm:px-6">
        <div class="flex w-full justify-between gap-x-15 mb-4">
          <div class="font-semibold text-2xl flex text-nowrap overflow-hidden">
            <template v-if="props.entities.length > 1">
              Moving {{ props.entities.length }} items
            </template>
            <template v-else>
              Moving "
              <div class="truncate max-w-[80%]">
                {{ props.entities[0].title }}
              </div>
              "
            </template>
          </div>
          <Button
            class="ml-auto"
            variant="ghost"
            @click="dialogType = ''"
          >
            <template #icon>
              <LucideX class="size-4" />
            </template>
          </Button>
        </div>
        <!-- <Combobox
          v-if="allFolders.data"
          v-model="folderSearch"
          class="mb-2"
          placeholder="Search for a folder"
          :options="
            allFolders.data.filter((k) =>
              currentFolder === ''
                ? k.label !== 'Home'
                : k.value !== currentFolder
            )
          "
        /> -->
        <Tabs
          v-model="tabIndex"
          as="div"
          :tabs="tabs"
        >
          <template #tab-panel>
            <div class="py-1 h-64 overflow-auto">
              <Tree
                v-for="k in tree.children"
                :key="k.value"
                node-key="value"
                :node="k"
              >
                <template
                  #node="{ node, hasChildren, isCollapsed, toggleCollapsed }"
                >
                  <div
                    class="flex items-center cursor-pointer select-none gap-1 h-7"
                    @click="openEntity(node.value)"
                  >
                    <div
                      ref="iconRef"
                      @click="toggleCollapsed($event)"
                    >
                      <LucideChevronDown
                        v-if="hasChildren && !isCollapsed"
                        class="size-3.5"
                      />
                      <LucideChevronRight
                        v-else-if="hasChildren"
                        class="size-3.5"
                      />
                      <div
                        v-else
                        class="ps-3.5"
                      />
                    </div>
                    <div
                      class="flex-grow rounded-sm text-base truncate h-full flex items-center pl-1"
                      :class="[
                        currentFolder === node.value
                          ? 'bg-surface-gray-3'
                          : 'hover:bg-surface-gray-2',
                        $store.state.currentFolder.name === node.value
                          ? 'cursor-not-allowed hover:bg-surface-white'
                          : 'group',
                      ]"
                    >
                      <LucideFolderClosed
                        v-if="isCollapsed"
                        class="mr-1 size-4"
                      />
                      <LucideFolder
                        v-else
                        class="mr-1 size-4"
                      />
                      <div
                        v-if="node.value === null"
                        class="overflow-visible"
                      >
                        <Input
                          v-model="node.label"
                          v-focus
                          type="text"
                          input-class=" !h-6"
                          @click.stop
                          @keydown.enter="openEntity(node)"
                        />
                      </div>
                      <span v-else
                        >{{ node.label }}
                        <em
                          v-if="$store.state.currentFolder.name === node.value"
                          >(current)</em
                        ></span
                      >
                      <Button
                        class="shrink hidden group-hover:block ml-auto"
                        :class="{
                          '!bg-surface-gray-3': currentFolder === node.value,
                        }"
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
                        <LucideFolderPlus class="size-4" />
                      </Button>
                    </div>
                  </div>
                </template>
              </Tree>
              <div
                v-if="!tree.children.length"
                class="text-base flex justify-center h-full"
              >
                <div class="self-center text-ink-gray-6 flex flex-col gap-2">
                  <LucideFolderClosed class="size-6 self-center" />
                  No folders found
                </div>
              </div>
            </div>
          </template>
        </Tabs>
        <div class="flex items-center justify-between pt-4">
          <div class="flex flex-col">
            <div class="flex items-center my-auto justify-start">
              <p class="text-sm pr-0.5">Moving to:</p>
              <Dropdown
                v-if="dropDownBreadcrumbs.length"
                class="h-7"
                :options="dropDownBreadcrumbs"
              >
                <Button variant="ghost">
                  <LucideEllipsis class="size-3.5" />
                </Button>
              </Dropdown>
              <span
                v-if="dropDownBreadcrumbs.length"
                class="text-ink-gray-5 mx-0.5"
              >
                {{ "/" }}
              </span>
              <div
                v-for="(crumb, index) in slicedBreadcrumbs"
                :key="index"
              >
                <span
                  v-if="breadcrumbs.length > 1 && index > 0"
                  class="text-ink-gray-5 mx-0.5"
                >
                  {{ "/" }}
                </span>
                <button
                  class="text-base cursor-pointer"
                  :class="
                    index === slicedBreadcrumbs.length - 1
                      ? 'text-ink-gray-9 text-base font-medium p-1'
                      : 'text-ink-gray-5 text-base rounded-[6px] hover:bg-surface-gray-2 p-1'
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
            :disabled="
              currentFolder === '' && breadcrumbs[0].title == $route.name
            "
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
              <LucideArrowLeftRight class="size-4" />
            </template>
            Move
          </Button>
        </div>
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
  Tree,
  Input,
} from "frappe-ui"
import { move, allFolders } from "@/resources/files"

import { useRoute } from "vue-router"
import { useStore } from "vuex"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideChevronDown from "~icons/lucide/chevron-down"
import LucideFolder from "~icons/lucide/folder"
import LucideHome from "~icons/lucide/home"
import LucideArrowLeftRight from "~icons/lucide/arrow-left-right"

const route = useRoute()

const emit = defineEmits(["success"])
const props = defineProps({
  entities: {
    type: Object,
    required: false,
    default: null,
  },
})
const dialogType = defineModel()
const open = ref(true)

const currentFolder = ref("")

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
  options: {
    isCollapsed: true,
  },
})
const teamRoot = reactive({
  name: "",
  label: "Team",
  children: [],
  options: {
    isCollapsed: true,
  },
})

allFolders.data.forEach((item) => {
  let map = item.is_private ? homeMap : teamMap
  const node = map[item.value]
  node.isCollapsed = true
  if (map[item.parent]) {
    map[item.parent].children.push(node)
  } else {
    ;(item.is_private ? homeRoot : teamRoot).children.push(node)
  }
})

const store = useStore()
const in_home = store.state.breadcrumbs[0].name == "Home"
const tabIndex = ref(in_home ? 0 : 1)
const tree = ref(tabIndex.value === 0 ? homeRoot : teamRoot)

const slicedBreadcrumbs = computed(() => {
  if (breadcrumbs.value.length > 3) {
    return breadcrumbs.value.slice(-3)
  }
  return breadcrumbs.value
})

const dropDownBreadcrumbs = computed(() => {
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
    icon: h(LucideHome, { class: "size-4" }),
  },
  {
    label: "Team",
    icon: h(LucideBuilding2, { class: "size-4" }),
  },
  // {
  //   label: "Favourites",
  //   icon: h(Star, { class: "size-4" }),
  // },
]

const breadcrumbs = ref([
  { name: "", title: in_home ? "Home" : "Team", is_private: in_home ? 1 : 0 },
])
const folderSearch = ref("")

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
    currentFolder.value = ""
    tree.value = tabIndex.value === 0 ? homeRoot : teamRoot
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
  if (store.state.currentFolder.name === node) return
  if (!node) {
    createdNode.value = node
    createFolder.fetch({
      title: node.label,
      personal: tabIndex.value === 0,
      parent: node.parent,
    })
  } else {
    currentFolder.value = node
    folderPermissions.fetch({
      entity_name: currentFolder.value,
    })
  }

  folderSearch.value = null
}

const expandNode = (obj, name) => {
  if (obj.value === name) {
    return obj
  }

  for (let k of obj.children) {
    let res = expandNode(k, name)
    if (res) {
      obj.isCollapsed = false
      return res
    }
  }
  return false
}

watch(folderSearch, (val) => {
  console.log(val)
  if (!val) return
  expandNode(tree.value, val)
  openEntity(val)
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
