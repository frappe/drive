<template>
  <div id="main" ref="container" @mousedown="(event) => handleMousedown(event)">
    <div v-for="(entities, i) in folderContents" :key="i">
      <span
        v-if="entities.length && Object.keys(entities).length > 1"
        class="text-base text-gray-600 font-medium leading-6 pl-1 my-0"
      >
        {{ i }}
      </span>

      <div v-if="entities.length" class="grid-container mt-2 mb-4">
        <div
          v-for="file in entities"
          :id="file.name"
          :key="file.name"
          class="rounded-lg border group select-none entity cursor-pointer relative group:"
          :class="[
            file.is_group && foldersBefore
              ? 'p-3 w-[162px] sm:w-[172px] h-[98px] sm:h-[108px]'
              : 'w-[162px] h-[162px] sm:w-[172px] sm:h-[172px]',
            selectedEntities.includes(file)
              ? 'bg-gray-100 border-gray-300'
              : 'border-gray-200 hover:shadow-xl',
          ]"
          draggable="false"
          @[action]="dblClickEntity(file)"
          @click="selectEntity(file, $event, displayOrderedEntities)"
          @dragstart="dragStart(file, $event)"
          @dragenter.prevent
          @dragover.prevent
          @mousedown.stop
          @contextmenu="
            handleEntityContext(file, $event, displayOrderedEntities)
          "
        >
          <Button
            :variant="'subtle'"
            :model-value="selectedEntities.includes(file)"
            class="z-10 duration-300 absolute visible group-hover:visible sm:invisible top-2 right-2"
            :class="[
              selectedEntities.includes(file)
                ? 'visible '
                : 'sm:bg-gray-100 visible sm:invisible',
            ]"
            @click.stop="
              handleEntityContext(file, $event, displayOrderedEntities)
            "
          >
            <FeatherIcon class="h-4" name="more-horizontal" />
          </Button>
          <GridItem
            :file_kind="file.file_kind"
            :mime_type="file.mime_type"
            :file_ext="file.file_ext"
            :name="file.name"
            :title="file.title"
            :modified="file.modified"
            :relative-modified="file.relativeModified"
            :file_size="file.file_size"
            :is_group="file.is_group"
            :color="file.color"
          />
        </div>
      </div>
    </div>
    <Button
      v-if="overrideCanLoadMore"
      class="w-full mx-auto text-base pt-8 pb-4"
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
import GridItem from "@/components/GridItem.vue"
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect"
import { FeatherIcon, Button } from "frappe-ui"
import { useInfiniteScroll } from "@vueuse/core"
import { ref } from "vue"

export default {
  name: "GridView",
  components: {
    GridItem,
    Button,
    FeatherIcon,
  },
  props: {
    folderContents: {
      type: Object,
      default: null,
    },
    folders: {
      type: Array,
      default: null,
    },
    files: {
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
        distance: 0,
        interval: 100,
        canLoadMore: () => props.overrideCanLoadMore,
      }
    )

    return { container, useInfiniteScroll }
  },
  data: () => ({
    selectionElementStyle: {},
    selectionCoordinates: { x1: 0, x2: 0, y1: 0, y2: 0 },
    containerRect: null,
  }),
  computed: {
    action() {
      if (window.innerWidth < 640) return "click"
      if (this.$store.state.singleClick) {
        return "click"
      } else {
        return "dblclick"
      }
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
  mounted() {
    if (this.isEmpty) return
    this.updateContainerRect()
    document.addEventListener("mousemove", this.handleMousemove)
    document.addEventListener("mouseup", this.handleMouseup)
    visualViewport.addEventListener("resize", this.updateContainerRect)

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
        this.selectedEntities.every((x) => x.owner === "You" || x.write)
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
        this.displayOrderedEntities
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
        this.selectedEntities.indexOf(entity) > -1
          ? this.selectedEntities.splice(
              this.selectedEntities.indexOf(entity),
              1
            )
          : this.selectedEntities.push(entity)
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
      this.emitter.emit("fetchFolderContents")
    },
  },
  resources: {
    moveEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        params: {
          method: "move",
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
<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(162px, 1fr));
  gap: 20px;
}
</style>
