<template>
  <div id="main" ref="container">
    <div
      class="hidden sm:grid items-center rounded bg-gray-100 min-h-7 p-2 overflow-hidden mb-2"
      :style="{ gridTemplateColumns: tableColumnsGridWidth }"
    >
      <div class="flex w-full items-center text-sm text-gray-600">Name</div>
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
    <div v-for="(entities, i) in folderContents" :key="i">
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
          class="entity grid items-center cursor-pointer rounded px-2 py-1.5 hover:bg-gray-50 group"
          :style="{
            gridTemplateColumns: tableColumnsGridWidth,
          }"
          :class="
            selectedEntities.includes(entity)
              ? 'bg-gray-100'
              : 'hover:bg-gray-100'
          "
          :draggable="false"
          @[action]="dblClickEntity(entity)"
          @click="selectEntity(entity, $event, displayOrderedEntities)"
          @contextmenu="
            handleEntityContext(entity, $event, displayOrderedEntities)
          "
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
<script>
import { Avatar, Button, FeatherIcon } from "frappe-ui"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useInfiniteScroll } from "@vueuse/core"
import { ref } from "vue"

export default {
  name: "ListView",
  components: {
    Avatar,
    Button,
    FeatherIcon,
  },
  props: {
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
  },
  emits: [
    "entitySelected",
    "openEntity",
    "showEntityContext",
    "showEmptyEntityContext",
    "fetchFolderContents",
    "updateOffset",
  ],
  setup(props, { emit }) {
    const container = ref(null)
    useInfiniteScroll(
      container,
      () => {
        emit("updateOffset")
      },
      {
        direction: "bottom",
        distance: 150,
        interval: 2000,
        canLoadMore: () => props.overrideCanLoadMore,
      }
    )
    return { container, useInfiniteScroll, formatMimeType, getIconUrl }
  },
  computed: {
    action() {
      if (window.innerWidth < 640) return "click"
      if (this.$store.state.singleClick) {
        return "click"
      } else {
        return "dblclick"
      }
    },
    tableColumnsGridWidth() {
      return window.innerWidth < 640
        ? "2fr 1fr 40px"
        : "2fr 1fr 150px 150px 40px"
    },
    isEmpty() {
      return !this.$store.state.currentViewEntites?.length
    },
    foldersBefore() {
      return this.$store.state.foldersBefore
    },
    displayOrderedEntities() {
      return this.$store.state.currentViewEntites
    },
  },
  methods: {
    selectEntity(entity, event, entities) {
      this.$emit("showEntityContext", null)
      this.$emit("showEmptyEntityContext", null)
      if (event.ctrlKey || event.metaKey) {
        /*  this.selectedEntities.indexOf(entity) > -1
          ? this.selectedEntities.splice(
              this.selectedEntities.indexOf(entity),
              1
            ) */
        if (this.selectedEntities.includes(entity)) {
          this.selectedEntities.pop(entity)
        } else {
          this.selectedEntities.push(entity)
        }
        this.$emit("entitySelected", this.selectedEntities)
        this.$store.commit("setEntityInfo", this.selectedEntities)
      } else if (event.shiftKey) {
        if (this.selectedEntities.includes(entity)) {
          return null
        }
        let shiftSelect
        this.selectedEntities.push(entity)
        const firstIndex = entities.indexOf(this.selectedEntities[0])
        const lastIndex = entities.indexOf(
          this.selectedEntities[this.selectedEntities.length - 1]
        )
        shiftSelect = entities.slice(firstIndex, lastIndex)
        if (firstIndex > lastIndex) {
          shiftSelect = entities.slice(lastIndex, firstIndex)
        } else {
          shiftSelect = entities.slice(firstIndex, lastIndex)
        }
        shiftSelect.slice(1).map((file) => {
          if (!this.selectedEntities.includes(file)) {
            this.selectedEntities.push(file)
          }
        })
        this.$emit("entitySelected", this.selectedEntities)
        this.$store.commit("setEntityInfo", this.selectedEntities)
      } else {
        this.$emit("entitySelected", [entity])
        this.$store.commit("setEntityInfo", [entity])
      }
    },
    dblClickEntity(entity) {
      this.$store.commit("setEntityInfo", [entity])
      this.$emit("openEntity", entity)
    },
    deselectAll() {
      this.$emit("entitySelected", [])
      this.$store.commit("setEntityInfo", [])
      this.$emit("showEntityContext", null)
      this.$emit("showEmptyEntityContext", null)
    },
    handleEntityContext(entity, event) {
      if (event.changedTouches) {
        event.clientX = event.changedTouches[0].clientX
        event.clientY = event.changedTouches[0].clientY
      }
      event.preventDefault(event)
      if (this.selectedEntities.length <= 1) {
        this.$emit("entitySelected", [entity])
        this.$store.commit("setEntityInfo", [entity])
      }
      this.$emit("showEntityContext", event)
    },
  },
}
</script>
