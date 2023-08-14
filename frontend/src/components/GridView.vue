<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div
      v-else
      ref="container"
      class="h-full px-5 md:px-0"
      @mousedown="(event) => handleMousedown(event)">
      <div v-if="folders.length > 0" class="mt-3">
        <div class="text-gray-600 font-medium">Folders</div>
        <div class="flex flex-row flex-wrap gap-5 mt-4">
          <div
            v-for="folder in folders"
            :id="folder.name"
            :key="folder.name"
            class="cursor-pointer p-2 w-44 h-30 rounded-lg border-2 group select-none entity"
            draggable="true"
            :class="
              selectedEntities.includes(folder)
                ? 'bg-green-100 border-[#5BB98C]'
                : 'border-gray-50 hover:shadow-2xl'
            "
            @dblclick="dblClickEntity(folder)"
            @click="selectEntity(folder, $event, displayOrderedEntities)"
            @contextmenu="
              handleEntityContext(folder, $event, displayOrderedEntities)
            "
            @dragstart="dragStart(folder, $event)"
            @drop="onDrop(folder)"
            @dragenter.prevent
            @dragover.prevent
            @mousedown.stop>
            <div class="flex items-start">
              <svg
                :style="{ fill: folder.color }"
                :draggable="false"
                width="30"
                height="30"
                viewBox="0 0 40 40"
                xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M19.8341 7.71154H3C2.72386 7.71154 2.5 7.9354 2.5 8.21154V34.75C2.5 35.8546 3.39543 36.75 4.5 36.75H35.5C36.6046 36.75 37.5 35.8546 37.5 34.75V4.75C37.5 4.47386 37.2761 4.25 37 4.25H24.7258C24.6719 4.25 24.6195 4.26739 24.5764 4.29957L20.133 7.61239C20.0466 7.67676 19.9418 7.71154 19.8341 7.71154Z" />
              </svg>
            </div>
            <div class="content-center grid">
              <span class="truncate text-sm font-medium mt-4">
                {{ folder.title }}
              </span>
              <p class="truncate text-xs text-gray-600 mt-2">
                {{ folder.file_size }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="files.length > 0"
        :class="folders.length > 0 ? 'mt-8' : 'mt-3'">
        <div class="text-gray-600 font-medium">Files</div>
        <div class="flex flex-row flex-wrap gap-5 mt-4">
          <div
            v-for="file in files"
            :id="file.name"
            :key="file.name"
            class="w-44 h-44 rounded-lg border-2 group select-none entity cursor-pointer"
            draggable="true"
            :class="
              selectedEntities.includes(file)
                ? 'bg-green-100 border-[#5BB98C]'
                : 'border-gray-50 hover:shadow-2xl'
            "
            @dblclick="dblClickEntity(file)"
            @click="selectEntity(file, $event, displayOrderedEntities)"
            @dragstart="dragStart(file, $event)"
            @dragenter.prevent
            @dragover.prevent
            @mousedown.stop
            @contextmenu="
              handleEntityContext(file, $event, displayOrderedEntities)
            ">
            <File
              :mime_type="file.mime_type"
              :file_ext="file.file_ext"
              :name="file.name"
              :title="file.title"
              :modified="file.modified" />
          </div>
        </div>
      </div>
    </div>
    <div
      id="selectionElement"
      class="h-20 w-20 absolute border-2 bg-green-100 border-[#5BB98C] opacity-50 mix-blend-multiply"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1" />
  </div>
</template>

<script>
import File from "@/components/File.vue";
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect";

export default {
  name: "GridView",
  components: {
    File,
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
  },
  emits: [
    "entitySelected",
    "openEntity",
    "showEntityContext",
    "showEmptyEntityContext",
    "fetchFolderContents",
  ],
  setup() {
    return;
  },
  data: () => ({
    selectionElementStyle: {},
    selectionCoordinates: { x1: 0, x2: 0, y1: 0, y2: 0 },
    containerRect: null,
  }),
  computed: {
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0;
    },
    folders() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 1)
        : [];
    },
    files() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 0)
        : [];
    },
    displayOrderedEntities() {
      return this.folders.concat(this.files);
    },
  },
  mounted() {
    if (this.isEmpty) return;
    this.updateContainerRect();
    document.addEventListener("mousemove", this.handleMousemove);
    document.addEventListener("mouseup", this.handleMouseup);
    visualViewport.addEventListener("resize", this.updateContainerRect);

    /* this.selectAllListener = (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "a" || e.key === "A"))
        this.$emit("entitySelected", this.folderContents);
    }; */

    this.copyListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "c" || e.key === "C") &&
        this.selectedEntities.length
      )
        this.$store.commit("setPasteData", {
          entities: this.selectedEntities.map((x) => x.name),
          action: "copy",
        });
    };

    this.cutListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "x" || e.key === "X") &&
        this.selectedEntities.length &&
        this.selectedEntities.every((x) => x.owner === "me" || x.write)
      )
        this.$store.commit("setPasteData", {
          entities: this.selectedEntities.map((x) => x.name),
          action: "cut",
        });
    };

    document.addEventListener("keydown", this.selectAllListener);
    document.addEventListener("keydown", this.copyListener);
    document.addEventListener("keydown", this.cutListener);
  },
  unmounted() {
    document.removeEventListener("keydown", this.selectAllListener);
    document.removeEventListener("keydown", this.copyListener);
    document.removeEventListener("keydown", this.cutListener);
  },
  methods: {
    handleMousedown(event) {
      this.deselectAll();
      this.selectionCoordinates.x1 = event.clientX;
      this.selectionCoordinates.y1 = event.clientY;
      this.selectionCoordinates.x2 = event.clientX;
      this.selectionCoordinates.y2 = event.clientY;
      this.selectionElementStyle = calculateRectangle(
        this.selectionCoordinates
      );
    },
    handleMousemove(event) {
      if (event.which != 1 || !this.selectionCoordinates.x1) return;
      this.selectionCoordinates.x2 = Math.max(
        this.containerRect.left,
        Math.min(this.containerRect.right, event.clientX)
      );
      this.selectionCoordinates.y2 = Math.max(
        this.containerRect.top,
        Math.min(this.containerRect.bottom, event.clientY)
      );
      this.selectionElementStyle = calculateRectangle(
        this.selectionCoordinates
      );
      const entityElements = this.$el.querySelectorAll(".entity");
      const selectedEntities = handleDragSelect(
        entityElements,
        this.selectionCoordinates,
        this.folderContents
      );
      this.$emit("entitySelected", selectedEntities);
      this.$store.commit(
        "setEntityInfo",
        selectedEntities[selectedEntities.length - 1]
      );
    },
    handleMouseup() {
      this.selectionCoordinates = { x1: 0, x2: 0, y1: 0, y2: 0 };
    },
    updateContainerRect() {
      this.containerRect = this.$refs["container"]?.getBoundingClientRect();
    },
    selectEntity(entity, event, entities) {
      this.$emit("showEntityContext", null);
      this.$emit("showEmptyEntityContext", null);
      let selectedEntities = this.selectedEntities;
      if (event.ctrlKey || event.metaKey) {
        const index = selectedEntities.indexOf(entity);
        index > -1
          ? selectedEntities.splice(index, 1)
          : selectedEntities.push(entity);
        this.$emit("entitySelected", selectedEntities);
      } else if (event.shiftKey) {
        let shiftSelect;
        selectedEntities.push(entity);
        const firstIndex = entities.indexOf(selectedEntities[0]);
        const lastIndex = entities.indexOf(
          selectedEntities[selectedEntities.length - 1]
        );
        if (firstIndex > lastIndex) {
          shiftSelect = entities.slice(lastIndex, firstIndex);
        } else {
          shiftSelect = entities.slice(firstIndex, lastIndex);
        }
        shiftSelect.slice(1).map((file) => {
          selectedEntities.push(file);
        });
      } else {
        selectedEntities = [entity];
        this.$emit("entitySelected", selectedEntities);
      }
      this.$store.commit(
        "setEntityInfo",
        selectedEntities[selectedEntities.length - 1]
      );
    },
    dblClickEntity(entity) {
      this.$store.commit("setEntityInfo", entity);
      this.$emit("openEntity", entity);
    },
    deselectAll() {
      this.$emit("entitySelected", []);
      this.$store.commit("setEntityInfo", null);
      this.$emit("showEntityContext", null);
    },
    handleEntityContext(entity, event, entities) {
      event.preventDefault(event);
      if (this.selectedEntities.length <= 1) {
        this.selectEntity(entity, event, entities);
      }
      console.log(entity);
      this.$store.commit("setEntityInfo", entity);
      this.$emit("showEntityContext", { x: event.clientX, y: event.clientY });
    },
    dragStart(entity, event) {
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.effectAllowed = "move";
      // for when a user directly drags a single file
      if (this.selectedEntities.length <= 1) {
        this.selectEntity(entity, event);
      }
    },

    async onDrop(newParent) {
      for (let i = 0; i < this.selectedEntities.length; i++) {
        if (this.selectedEntities[i].name === newParent.name) {
          continue;
        }
        await this.$resources.moveEntity.submit({
          method: "move",
          entity_name: this.selectedEntities[i].name,
          new_parent: newParent.name,
        });
      }
      this.deselectAll();
      this.$emit("fetchFolderContents");
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
            return "New parent is required";
          }
        },
      };
    },
  },
};
</script>
