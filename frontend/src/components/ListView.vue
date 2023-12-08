<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div
      v-else
      ref="container"
      @mousedown="(event) => handleMousedown(event)"
      class="h-full">
      <div
        class="mb-1 grid items-center rounded bg-gray-100 py-2 pl-2 pr-4 overflow-x-hidden"
        :style="{ gridTemplateColumns: tableColumnsGridWidth }">
        <Checkbox
          class="cursor-pointer duration-300 z-10"
          :modelValue="
            selectedEntities?.length > 1 &&
            selectedEntities?.length === folderContents?.length
          "
          @click.stop="toggleSelectAll" />
        <div class="flex w-full items-center text-base text-gray-600">Name</div>
        <div
          class="flex w-full items-center justify-start text-base text-gray-600">
          Owner
        </div>
        <div
          class="flex w-full items-center justify-end text-base text-gray-600">
          Last Modified
        </div>
        <div
          class="flex w-full items-center justify-end text-base text-gray-600">
          Size
        </div>
      </div>
      <div
        v-for="entity in folderContents"
        :id="entity.name"
        :key="entity.name"
        class="entity grid items-center cursor-pointer mb-1 rounded pl-2 pr-4 py-1.5 hover:bg-gray-50 group"
        :style="{
          gridTemplateColumns: tableColumnsGridWidth,
        }"
        :class="
          selectedEntities.includes(entity)
            ? 'bg-gray-100'
            : 'hover:bg-gray-100'
        "
        :draggable="true"
        @dblclick="dblClickEntity(entity)"
        @click="selectEntity(entity, $event, folderContents)"
        @contextmenu="handleEntityContext(entity, $event, folderContents)"
        @dragstart="dragStart(entity, $event)"
        @dragenter.prevent
        @dragover.prevent
        @mousedown.stop
        @drop="isGroupOnDrop(entity)">
        <Checkbox
          :modelValue="selectedEntities.includes(entity)"
          class="duration-300 invisible group-hover:visible checked:visible" />
        <div
          class="flex items-center text-gray-800 text-sm font-medium truncate"
          :draggable="false">
          <svg
            v-if="entity.is_group"
            :style="{ fill: entity.color }"
            :draggable="false"
            class="h-[20px] mr-3"
            viewBox="0 0 30 30"
            xmlns="http://www.w3.org/2000/svg">
            <path
              d="M14.8341 5.40865H2.375C2.09886 5.40865 1.875 5.63251 1.875 5.90865V25.1875C1.875 26.2921 2.77043 27.1875 3.875 27.1875H26.125C27.2296 27.1875 28.125 26.2921 28.125 25.1875V3.3125C28.125 3.03636 27.9011 2.8125 27.625 2.8125H18.5651C18.5112 2.8125 18.4588 2.82989 18.4156 2.86207L15.133 5.30951C15.0466 5.37388 14.9418 5.40865 14.8341 5.40865Z" />
          </svg>
          <img
            v-else
            :src="getIconUrl(formatMimeType(entity.mime_type))"
            :draggable="false"
            class="h-[20px] mr-3" />
          {{ entity.title }}
        </div>
        <div
          class="flex items-center justify-start text-gray-800 text-sm font-medium truncate">
          <Avatar
            :image="entity.user_image"
            :label="entity.full_name"
            class="mr-2"
            size="lg" />
          {{ entity.owner }}
        </div>
        <div
          class="flex items-center justify-end text-gray-800 text-sm font-medium truncate">
          {{ entity.modified }}
        </div>
        <div class="flex w-full justify-end text-base text-gray-600">
          {{ entity.file_size }}
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
import { Avatar, Checkbox } from "frappe-ui";
import { formatMimeType } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect";

export default {
  name: "GridView",
  components: {
    Checkbox,
    Avatar,
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
    return { formatMimeType, getIconUrl };
  },
  data: () => ({
    selectionElementStyle: {},
    selectionCoordinates: { x1: 0, x2: 0, y1: 0, y2: 0 },
    containerRect: null,
    tableColumnsGridWidth: "25px 2fr 1fr 100px 100px",
  }),
  computed: {
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0;
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
        });
    };

    this.cutListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "x" || e.key === "X") &&
        this.selectedEntities.length &&
        this.selectedEntities.every((x) => x.owner === "Me")
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
    toggleSelectAll() {
      let selectAllEntites = [];
      selectAllEntites = [...this.folderContents];
      this.$emit("entitySelected", selectAllEntites);
      this.$store.commit("setEntityInfo", selectAllEntites);
    },
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
    getFileSubtitle(file) {
      let fileSubtitle = formatMimeType(file.mime_type);
      fileSubtitle =
        fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1);
      return `${fileSubtitle} ∙ ${file.modified}`;
    },
    selectEntity(entity, event, entities) {
      this.$emit("showEntityContext", null);
      this.$emit("showEmptyEntityContext", null);
      if (event.ctrlKey || event.metaKey) {
        /*  this.selectedEntities.indexOf(entity) > -1
          ? this.selectedEntities.splice(
              this.selectedEntities.indexOf(entity),
              1
            ) */
        if (this.selectedEntities.includes(entity)) {
          this.selectedEntities.pop(entity);
        } else {
          this.selectedEntities.push(entity);
        }
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
    isGroupOnDrop(entity) {
      return entity.is_group ? this.onDrop(entity) : null;
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
