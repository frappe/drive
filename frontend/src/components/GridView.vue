<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div
      v-else
      ref="container"
      class="h-full"
      @mousedown="(event) => handleMousedown(event)">
      <div v-if="folders.length > 0" class="mt-3">
        <div class="text-gray-600 font-medium">Folders</div>
        <div class="flex flex-row flex-wrap gap-4 mt-4">
          <div
            v-for="folder in folders"
            :id="folder.name"
            :key="folder.name"
            class="cursor-pointer p-2 w-36 h-22 rounded-lg border group select-none entity"
            draggable="true"
            :class="
              selectedEntities.includes(folder)
                ? 'bg-gray-100 border-gray-300'
                : 'border-gray-200 hover:shadow-2xl'
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
                class="h-6 w-auto"
                viewBox="0 0 30 30"
                fill="none"
                xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z" />
              </svg>
              <Checkbox
                :modelValue="selectedEntities.includes(folder)"
                class="duration-300 relative ml-auto invisible group-hover:visible checked:visible" />
            </div>
            <div class="content-center grid">
              <span class="truncate text-sm text-gray-800 mt-2">
                {{ folder.title }}
              </span>
              <p class="truncate text-xs text-gray-600 mt-0">
                {{ folder.file_size }} {{ !!folder.file_size ? "∙" : null }}
                {{ folder.modified }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="files.length > 0"
        :class="folders.length > 0 ? 'mt-8' : 'mt-3'">
        <div class="text-gray-600 font-medium">Files</div>
        <div class="inline-flex flex-row flex-wrap gap-4 mt-4">
          <div
            v-for="file in files"
            :id="file.name"
            :key="file.name"
            class="w-36 h-36 rounded-lg border group select-none entity cursor-pointer relative group:"
            draggable="true"
            :class="
              selectedEntities.includes(file)
                ? 'bg-gray-100 border-gray-300'
                : 'border-gray-200 hover:shadow-2xl'
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
            <Checkbox
              :modelValue="selectedEntities.includes(file)"
              class="duration-300 display-none absolute right-1 top-1 invisible group-hover:visible checked:visible" />
            <File
              :mime_type="file.mime_type"
              :file_ext="file.file_ext"
              :name="file.name"
              :title="file.title"
              :modified="file.modified"
              :file_size="file.file_size" />
          </div>
        </div>
      </div>
    </div>
    <div
      id="selectionElement"
      class="h-20 w-20 absolute border-1 bg-gray-300 border-gray-400 opacity-50 mix-blend-multiply rounded"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1" />
  </div>
</template>

<script>
import File from "@/components/File.vue";
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect";
import { Checkbox } from "frappe-ui";
import Select from "frappe-ui/src/components/Select.vue";

export default {
  name: "GridView",
  components: {
    File,
    Checkbox,
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
        this.selectedEntities.every((x) => x.owner === "Me" || x.write)
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
      this.$store.commit("setEntityInfo", selectedEntities);
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
      if (event.ctrlKey || event.metaKey) {
        this.selectedEntities.indexOf(entity) > -1
          ? this.selectedEntities.splice(
              this.selectedEntities.indexOf(entity),
              1
            )
          : this.selectedEntities.push(entity);
        this.$emit("entitySelected", this.selectedEntities);
        this.$store.commit("setEntityInfo", this.selectedEntities);
      } else if (event.shiftKey) {
        if (this.selectedEntities.includes(entity)) {
          return null;
        }
        let shiftSelect;
        this.selectedEntities.push(entity);
        const firstIndex = entities.indexOf(this.selectedEntities[0]);
        const lastIndex = entities.indexOf(
          this.selectedEntities[this.selectedEntities.length - 1]
        );
        shiftSelect = entities.slice(firstIndex, lastIndex);
        if (firstIndex > lastIndex) {
          shiftSelect = entities.slice(lastIndex, firstIndex);
        } else {
          shiftSelect = entities.slice(firstIndex, lastIndex);
        }
        shiftSelect.slice(1).map((file) => {
          if (!this.selectedEntities.includes(file)) {
            this.selectedEntities.push(file);
          }
        });
        this.$emit("entitySelected", this.selectedEntities);
        this.$store.commit("setEntityInfo", this.selectedEntities);
      } else {
        this.$emit("entitySelected", [entity]);
        this.$store.commit("setEntityInfo", [entity]);
      }
    },
    dblClickEntity(entity) {
      this.$store.commit("setEntityInfo", [entity]);
      this.$emit("openEntity", entity);
    },
    deselectAll() {
      this.$emit("entitySelected", []);
      this.$store.commit("setEntityInfo", []);
      this.$emit("showEntityContext", null);
      this.$emit("showEmptyEntityContext", null);
    },
    handleEntityContext(entity, event, entities) {
      event.preventDefault(event);
      if (this.selectedEntities.length <= 1) {
        this.$emit("entitySelected", [entity]);
        this.$store.commit("setEntityInfo", [entity]);
      }
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
