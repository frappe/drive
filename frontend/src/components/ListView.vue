<template>
  <div
    v-if="isEmpty"
    class="h-full flex flex-col overflow-y-hidden mt-3.5 px-4 pb-8"
  >
    <slot name="toolbar"></slot>
    <slot name="placeholder"></slot>
  </div>

  <div
    v-else
    ref="container"
    class="h-full overflow-y-auto mt-3.5 px-4 pb-5"
    @mousedown.passive="(event) => handleMousedown(event)"
  >
    <slot name="toolbar"></slot>
    <!--       class="mb-2 grid items-center space-x-4 rounded bg-gray-100 p-2"
 -->
    <div
      class="sticky hidden sm:grid top-0 z-10 items-center rounded bg-gray-100 min-h-7 p-2 overflow-hidden mb-2"
      :style="{ gridTemplateColumns: tableColumnsGridWidth }"
    >
      <!-- <Checkbox
        class="cursor-pointer duration-300 z-10"
        :modelValue="
          selectedEntities?.length > 1 &&
          selectedEntities?.length === folderContents?.length
        "
        @click.stop="toggleSelectAll" /> -->
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
      <!-- Use the listview api if this needs to be switched in more views -->
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
    <div v-for="entity in folderContents" :key="entity.name">
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
        :draggable="true"
        @[action]="dblClickEntity(entity)"
        @click="selectEntity(entity, $event, folderContents)"
        @contextmenu="handleEntityContext(entity, $event, folderContents)"
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
    <Button
      v-if="overrideCanLoadMore"
      class="w-full mx-auto text-base pt-8 pb-6"
      :loading="true"
      :disabled="true"
      variant="ghost"
      >Loading</Button
    >
    <div
      id="selectionElement"
      class="h-20 w-20 absolute border-1 bg-gray-300 border-gray-400 opacity-50 mix-blend-multiply rounded"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1"
    />
  </div>
</template>
<script>
import { Avatar, Button, FeatherIcon } from "frappe-ui"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useInfiniteScroll } from "@vueuse/core"
import { ref } from "vue"
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect"

export default {
  name: "ListView",
  components: {
    Avatar,
    Button,
    FeatherIcon,
  },
  props: {
    folderContents: {
      type: Array,
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
  data: () => ({
    selectionElementStyle: {},
    selectionCoordinates: { x1: 0, x2: 0, y1: 0, y2: 0 },
    containerRect: null,
  }),
  computed: {
    action() {
      return window.innerWidth < 640 ? "click" : "dblclick"
    },
    tableColumnsGridWidth() {
      return window.innerWidth < 640
        ? "2fr 1fr 40px"
        : "2fr 1fr 150px 150px 40px"
    },
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0
    },
  },
  mounted() {
    if (this.isEmpty) return
    this.updateContainerRect()
    document.addEventListener("mousemove", this.handleMousemove)
    document.addEventListener("mouseup", this.handleMouseup)
    visualViewport.addEventListener("resize", this.updateContainerRect)

    /* this.selectAllListener = (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "a" || e.key === "A"))
        this.$emit("entitySelected", this.folderContents);
    };
 */
    this.copyListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "c" || e.key === "C") &&
        this.selectedEntities.length
      )
        this.$store.commit("setPasteData", {
          entities: this.selectedEntities.map((x) => x.name),
          action: "copy",
        })
    }

    this.cutListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "x" || e.key === "X") &&
        this.selectedEntities.length &&
        this.selectedEntities.every((x) => x.owner === "You")
      )
        this.$store.commit("setPasteData", {
          entities: this.selectedEntities.map((x) => x.name),
          action: "cut",
        })
    }

    document.addEventListener("keydown", this.selectAllListener)
    document.addEventListener("keydown", this.copyListener)
    document.addEventListener("keydown", this.cutListener)
  },
  unmounted() {
    document.removeEventListener("keydown", this.selectAllListener)
    document.removeEventListener("keydown", this.copyListener)
    document.removeEventListener("keydown", this.cutListener)
  },
  methods: {
    toggleSelectAll() {
      let selectAllEntites = []
      selectAllEntites = [...this.folderContents]
      this.$emit("entitySelected", selectAllEntites)
      this.$store.commit("setEntityInfo", selectAllEntites)
    },
    handleMousedown(event) {
      this.deselectAll()
      this.selectionCoordinates.x1 = event.clientX
      this.selectionCoordinates.y1 = event.clientY
      this.selectionCoordinates.x2 = event.clientX
      this.selectionCoordinates.y2 = event.clientY
      this.selectionElementStyle = calculateRectangle(this.selectionCoordinates)
    },
    handleMousemove(event) {
      if (event.which != 1 || !this.selectionCoordinates.x1) return
      this.selectionCoordinates.x2 = Math.max(
        this.containerRect.left,
        Math.min(this.containerRect.right, event.clientX)
      )
      this.selectionCoordinates.y2 = Math.max(
        this.containerRect.top,
        Math.min(this.containerRect.bottom, event.clientY)
      )
      this.selectionElementStyle = calculateRectangle(this.selectionCoordinates)
      const entityElements = this.$el.querySelectorAll(".entity")
      const selectedEntities = handleDragSelect(
        entityElements,
        this.selectionCoordinates,
        this.folderContents
      )
      this.$emit("entitySelected", selectedEntities)
      this.$store.commit("setEntityInfo", selectedEntities)
    },
    handleMouseup() {
      this.selectionCoordinates = { x1: 0, x2: 0, y1: 0, y2: 0 }
    },
    updateContainerRect() {
      this.containerRect = this.$refs["container"]?.getBoundingClientRect()
    },
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
      let clientX = event.clientX
      let clientY = event.clientY
      if (event.changedTouches) {
        clientX = event.changedTouches[0].clientX
        clientY = event.changedTouches[0].clientY
      }
      event.preventDefault(event)
      if (this.selectedEntities.length <= 1) {
        this.$emit("entitySelected", [entity])
        this.$store.commit("setEntityInfo", [entity])
      }
      this.$emit("showEntityContext", { x: clientX, y: clientY })
    },
    dragStart(entity, event) {
      event.dataTransfer.dropEffect = "move"
      event.dataTransfer.effectAllowed = "move"
      // for when a user directly drags a single file
      if (this.selectedEntities.length <= 1) {
        this.selectEntity(entity, event)
      }
    },
    async onDrop(newParent) {
      for (let i = 0; i < this.selectedEntities.length; i++) {
        if (this.selectedEntities[i].name === newParent.name) {
          continue
        }
        await this.$resources.moveEntity.submit({
          method: "move",
          entity_name: this.selectedEntities[i].name,
          new_parent: newParent.name,
        })
      }
      this.deselectAll()
      this.emitter.emit("fetchFolderContents")
    },
    isGroupOnDrop(entity) {
      return entity.is_group ? this.onDrop(entity) : null
    },
  },
  resources: {
    moveEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        params: {
          method: "move",
          entity_name: "entity name",
          new_parent: "new entity parent",
        },
        validate(params) {
          if (!params?.new_parent) {
            return "New parent is required"
          }
        },
      }
    },
  },
}
</script>
