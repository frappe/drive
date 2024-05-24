<template>
  <div
    v-if="isEmpty"
    class="h-full flex flex-col overflow-y-hidden pt-3.5 px-4 pb-8"
  >
    <slot name="toolbar"></slot>
    <slot name="placeholder"></slot>
  </div>
  <div
    v-else
    ref="container"
    class="h-full flex flex-col overflow-y-auto pt-3.5 px-4 pb-8"
    @mousedown="(event) => handleMousedown(event)"
  >
    <slot name="toolbar"></slot>
    <div v-if="folders.length > 0">
      <div class="text-gray-600 font-medium mt-6.5">Folders</div>
      <div class="flex flex-row flex-wrap gap-5 mt-2">
        <div
          v-for="folder in folders"
          :id="folder.name"
          :key="folder.name"
          class="cursor-pointer p-3 w-[172px] h-[108px] rounded-lg border group select-none entity"
          draggable="true"
          :class="
            selectedEntities.includes(folder)
              ? 'bg-gray-100 border-gray-300'
              : 'border-gray-200 hover:shadow-xl'
          "
          @[action]="dblClickEntity(folder)"
          @click="selectEntity(folder, $event, displayOrderedEntities)"
          @contextmenu="
            handleEntityContext(folder, $event, displayOrderedEntities)
          "
          @dragstart="dragStart(folder, $event)"
          @drop="onDrop(folder)"
          @dragenter.prevent
          @dragover.prevent
          @mousedown.stop
        >
          <div class="flex items-start">
            <svg
              class="h-7.5 w-auto"
              :draggable="false"
              :style="{ fill: folder.color }"
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
            <Button
              :variant="'subtle'"
              :model-value="selectedEntities.includes(folder)"
              :class="
                selectedEntities.includes(folder)
                  ? 'visible bg-gray-300'
                  : 'bg-inherit sm:bg-gray-100 visible sm:invisible'
              "
              class="border-1 duration-300 relative ml-auto visible group-hover:visible sm:invisible"
              @click.stop="
                handleEntityContext(folder, $event, displayOrderedEntities)
              "
            >
              <FeatherIcon class="h-4" name="more-horizontal" />
            </Button>
          </div>
          <div class="content-center grid mt-3.5">
            <span class="truncate text-base font-medium text-gray-800">
              {{ folder.title }}
            </span>
            <p
              :title="folder.modified"
              class="truncate text-sm text-gray-600 mt-2"
            >
              {{ folder.file_size ? folder.file_size + " ∙ " : "" }}
              {{ folder.relativeModified }}
            </p>
          </div>
        </div>
      </div>
    </div>
    <div v-if="files.length > 0" :class="folders.length > 0 ? 'mt-8' : 'mt-3'">
      <div class="text-gray-600 font-medium">Files</div>
      <div class="inline-flex flex-row flex-wrap gap-5 mt-4">
        <div
          v-for="file in files"
          :id="file.name"
          :key="file.name"
          class="w-[172px] h-[172px] rounded-lg border group select-none entity cursor-pointer relative group:"
          draggable="true"
          :class="
            selectedEntities.includes(file)
              ? 'bg-gray-100 border-gray-300'
              : 'border-gray-200 hover:shadow-xl'
          "
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
            :class="
              selectedEntities.includes(file)
                ? 'visible '
                : 'sm:bg-gray-100 visible sm:invisible'
            "
            class="z-10 duration-300 absolute right-0 mr-1.5 mt-1.5 visible group-hover:visible sm:invisible"
            @click.stop="
              handleEntityContext(file, $event, displayOrderedEntities)
            "
          >
            <FeatherIcon class="h-4" name="more-horizontal" />
          </Button>
          <File
            :file_kind="file.file_kind"
            :mime_type="file.mime_type"
            :file_ext="file.file_ext"
            :name="file.name"
            :title="file.title"
            :modified="file.modified"
            :relative-modified="file.relativeModified"
            :file_size="file.file_size"
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
import File from "@/components/File.vue"
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect"
import { FeatherIcon, Button } from "frappe-ui"
import { useInfiniteScroll } from "@vueuse/core"
import { ref } from "vue"

export default {
  name: "GridView",
  components: {
    File,
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

    return { container, useInfiniteScroll }
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
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0
    },
    folders() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 1)
        : []
    },
    files() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 0)
        : []
    },
    displayOrderedEntities() {
      return this.folders.concat(this.files)
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
