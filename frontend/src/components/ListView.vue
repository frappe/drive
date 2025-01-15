<template>
  <div id="main" ref="container">
    <div
      class="hidden sm:grid items-center rounded bg-gray-100 min-h-7 p-2 overflow-hidden mb-2"
      :style="{ gridTemplateColumns: tableColumnsGridWidth }"
    >
      <div
        class="flex w-full items-center text-sm text-gray-600"
        @mouseenter="() => (selectAllHover = true)"
        @mouseleave="() => (selectAllHover = false)"
      >
        <div class="w-4 h-4 ml-1 mr-3 my-1">
          <input
            @click="selectAll"
            :checked="
              selectedEntities.length ===
              Object.values(folderContents).reduce(
                (l, g) => l + g?.length || 0,
                0
              )
            "
            type="checkbox"
            class="border-gray-300 rounded-sm mr-4"
            :class="{ hidden: !multi && !selectAllHover }"
          />
        </div>
        Name
      </div>
      <div class="flex w-full items-center justify-start text-sm text-gray-600">
        Owner
      </div>
      <div
        v-if="$route.name === 'Recents'"
        class="flex w-full items-center justify-end text-sm text-gray-600"
      >
        Last Accessed
      </div>
      <div
        v-else
        class="flex w-full items-center justify-end text-sm text-gray-600"
      >
        Last Modified
      </div>
      <div class="flex w-full items-center justify-end text-sm text-gray-600">
        Size
      </div>
      <div />
    </div>
    <Loader v-if="!folderContents || folderContents['All Files'] === null" />
    <div v-else v-for="(entities, i) in folderContents" :key="i">
      <div
        v-if="Object.keys(folderContents).length > 1 && entities.length"
        class="flex items-center w-full py-1.5 pr-2"
      >
        <span class="text-base text-gray-600 font-medium leading-6 pl-1.5">
          {{ i }}
        </span>
      </div>

      <div
        v-if="Object.keys(folderContents).length > 1 && entities.length"
        class="mx-2 h-px border-t border-gray-200"
      ></div>
      <div v-for="entity in entities" :key="entity.name">
        <div
          :id="entity.name"
          :key="entity.name"
          class="entity grid items-center cursor-pointer rounded-sm px-2 py-1.5 group"
          :style="{
            gridTemplateColumns: tableColumnsGridWidth,
          }"
          :class="
            selectedEntities.includes(entity)
              ? 'bg-gray-300'
              : 'hover:bg-gray-50'
          "
          :draggable="false"
          @[action]="dblClickEntity(entity, $event)"
          @click="!multi && selectEntity(entity, $event)"
          @contextmenu="handleEntityContext(entity, $event)"
          @mouseenter="() => (hoveredRow = entity.name)"
          @mouseleave="() => (hoveredRow = '')"
          @dragstart="dragStart(entity, $event)"
          @dragenter.prevent
          @dragover.prevent
          @mousedown.stop
          @drop="isGroupOnDrop(entity)"
        >
          <div
            class="flex items-center text-gray-800 text-base font-medium truncate"
            :draggable="false"
          >
            <div class="w-4 h-4 ml-1 mr-3 my-1">
              <input
                type="checkbox"
                @click="checkboxSelect(entity, $event)"
                :checked="multi && selectedEntities.includes(entity)"
                class="checked:bg-black-400 border-gray-300 rounded-sm mr-4 focus:ring-0"
                :class="{ hidden: !multi && entity.name !== hoveredRow }"
              />
            </div>
            <svg
              v-if="entity.is_group"
              class="h-auto w-5 mr-3"
              :draggable="false"
              :style="{ fill: entity.color }"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g clip-path="url(#clip0_1942_59507)">
                <path
                  d="M7.83412 2.88462H1.5C1.22386 2.88462 1 3.10847 1 3.38462V12.5C1 13.6046 1.89543 14.5 3 14.5H13C14.1046 14.5 15 13.6046 15 12.5V2C15 1.72386 14.7761 1.5 14.5 1.5H9.94008C9.88623 1.5 9.83382 1.51739 9.79065 1.54957L8.13298 2.78547C8.04664 2.84984 7.94182 2.88462 7.83412 2.88462Z"
                />
              </g>
              <defs>
                <clipPath id="clip0_1942_59507">
                  <rect width="16" height="16" fill="white" />
                </clipPath>
              </defs>
            </svg>
            <img
              v-else
              :src="getIconUrl(formatMimeType(entity.mime_type))"
              :draggable="false"
              class="h-[20px] mr-3"
            />
            {{ entity.title }}
            <div
              v-if="
                selectedEntities.length <= 1 &&
                (entity.name === hoveredRow ||
                  selectedEntities.includes(entity))
              "
              class="justify-content-end ml-auto mr-2"
              @click="toggleFavorite([entity])"
            >
              <FeatherIcon
                name="star"
                class="h-4"
                :class="{
                  'stroke-yellow-500 fill-yellow-500': entity.is_favourite,
                }"
              />
            </div>
          </div>
          <div
            class="hidden sm:flex items-center justify-start text-gray-700 text-base truncate"
          >
            <Avatar
              :image="entity.user_image"
              :label="entity.full_name"
              class="-relative mr-2"
              size="sm"
            />
            {{ entity.owner }}
          </div>
          <div
            :title="entity.modified"
            class="hidden sm:flex items-center justify-end text-gray-700 text-base truncate"
          >
            {{ entity.relativeModified }}
          </div>
          <div class="flex w-full justify-end text-base text-gray-700">
            {{ entity.file_size }}
          </div>
          <div class="flex w-full justify-end">
            <Button
              :variant="'ghost'"
              :model-value="selectedEntities.includes(entity)"
              :class="
                selectedEntities.includes(entity)
                  ? 'visible bg-gray-300'
                  : 'bg-inherit visible'
              "
              class="border-1 duration-300 relative ml-auto visible group-hover:visible"
              @click.stop="
                handleEntityContext(entity, $event, displayOrderedEntities)
              "
            >
              <FeatherIcon class="h-4" name="more-horizontal" />
            </Button>
          </div>
        </div>
        <div class="mx-2 h-px border-t border-gray-200"></div>
      </div>
    </div>
    <Button
      v-if="overrideCanLoadMore"
      class="w-full mx-auto text-base pt-8 pb-6"
      :loading="true"
      :disabled="true"
      variant="ghost"
      >Loading</Button
    >
  </div>
</template>
<script setup>
import { Avatar, Button, FeatherIcon } from "frappe-ui"
import Loader from "@/components/Loader.vue"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useInfiniteScroll } from "@vueuse/core"
import { useStore } from "vuex"
import { ref, computed } from "vue"
import { toggleFav } from "@/stores/listView"
import { toast, toastError } from "@/utils/toasts.js"

const store = useStore()

const hoveredRow = ref("")
const selectAllHover = ref(false)
const multi = ref(false)
const container = ref(null)

const action = computed(() =>
  window.innerWidth < 640 || store.state.singleClick ? "click" : "dblclick"
)
const tableColumnsGridWidth = computed(() =>
  window.innerWidth < 640 ? "2fr 1fr 40px" : "2fr 1fr 150px 150px 40px"
)
const displayOrderedEntities = computed(() => store.state.currentViewEntites)

const emit = defineEmits([
  "entitySelected",
  "openEntity",
  "showEntityContext",
  "showEmptyEntityContext",
  "fetchFolderContents",
  "updateOffset",
  "update-multi",
])

const props = defineProps({
  folderContents: {
    type: Object,
    default: null,
  },
  selectedEntities: {
    type: Array,
    default: null,
  },
  overrideCanLoadMore: {
    type: Boolean,
    default: false,
  },
})

useInfiniteScroll(container, () => emit("updateOffset"), {
  direction: "bottom",
  distance: 150,
  interval: 2000,
  canLoadMore: () => props.overrideCanLoadMore,
})

document.onkeydown = (e) => {
  if (e.key === "ArrowDown") {
    console.log(props.selectedEntities)
    const current = props.selectedEntities[0].name
    const index = store.state.currentViewEntites.findIndex(
      ({ name }) => name === current
    )
    console.log(store.state.currentViewEntites[index + 1])
  }
}

function toggleFavorite(entities) {
  const direction = !entities[0].is_favourite
  console.log(direction)
  entities.forEach((e) => (e.is_favourite = direction))
  toggleFav.submit(
    {
      entities: entities.map((e) => ({
        name: e.name,
        is_favourite: e.is_favourite,
      })),
    },
    {
      onError: () => {
        toastError("Failed to update favourites")
      },
      onSuccess: () => {
        if (!direction) {
          toast(
            `${
              props.selectedEntities.length > 1
                ? props.selectedEntities.length + " items removed"
                : "Removed"
            } from Favourites`
          )
        } else {
          toast(
            `${
              props.selectedEntities.length > 1
                ? props.selectedEntities.length + " items added"
                : "Added"
            } to Favourites`
          )
        }
      },
    }
  )
}

function checkboxSelect(entity, event) {
  multi.value = true
  emit("update-multi", true)
  event.stopPropagation()
  this.selectEntity(entity, event)
  if (!document.querySelector("input[type=checkbox]:checked")) {
    multi.value = false
    emit("update-multi", false)
  }
}

function selectEntity(entity, event) {
  emit("showEntityContext", null)
  emit("showEmptyEntityContext", null)

  if (multi || event.ctrlKey || event.metaKey) {
    if (props.selectedEntities.includes(entity)) {
      props.selectedEntities.splice(props.selectedEntities.indexOf(entity), 1)
    } else {
      props.selectedEntities.push(entity)
    }
    emit("entitySelected", props.selectedEntities)
    store.commit("setEntityInfo", props.selectedEntities)
  } else if (event.shiftKey) {
    if (props.selectedEntities.includes(entity)) return null

    props.selectedEntities.push(entity)

    const entities = store.state.currentViewEntites
    const firstIndex = entities.indexOf(props.selectedEntities[0])
    const lastIndex = entities.indexOf(
      props.selectedEntities[props.selectedEntities.length - 1]
    )

    let shiftSelect = entities.slice(firstIndex, lastIndex)

    if (firstIndex > lastIndex) {
      shiftSelect = entities.slice(lastIndex, firstIndex)
    } else {
      shiftSelect = entities.slice(firstIndex, lastIndex)
    }
    shiftSelect.slice(1).map((file) => {
      if (!props.selectedEntities.includes(file)) {
        props.selectedEntities.push(file)
      }
    })
    emit("entitySelected", props.selectedEntities)
    store.commit("setEntityInfo", props.selectedEntities)
  } else {
    props.selectedEntities = [entity]
    emit("entitySelected", props.selectedEntities)
    store.commit("setEntityInfo", props.selectedEntities)
  }
}

function dblClickEntity(entity, event) {
  if (multi || event.target.type === "checkbox") return null
  store.commit("setEntityInfo", [entity])
  emit("openEntity", entity)
}

function selectAll() {
  if (props.selectedEntities.length) {
    props.selectedEntities.splice(0, props.selectedEntities.length)
    multi.value = false
    emit("update-multi", false)
  } else {
    for (let group in props.folderContents) {
      props.folderContents[group].forEach((entity) => {
        props.selectedEntities.push(entity)
      })
      multi.value = true
      emit("update-multi", true)
    }
  }
  emit("entitySelected", props.selectedEntities)
  store.commit("setEntityInfo", props.selectedEntities)
  emit("showEntityContext", null)
  emit("showEmptyEntityContext", null)
}

function handleEntityContext(entity, event) {
  if (event.changedTouches) {
    event.clientX = event.changedTouches[0].clientX
    event.clientY = event.changedTouches[0].clientY
  }
  event.preventDefault()

  if (props.selectedEntities.length <= 1) {
    emit("entitySelected", [entity])
    store.commit("setEntityInfo", [entity])
  }
  emit("showEntityContext", event)
}
</script>
