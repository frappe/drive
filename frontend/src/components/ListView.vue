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
      <table class="max-h-full min-w-full">
        <thead
          class="sticky top-0 bg-white shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-200">
          <tr class="text-left text-base text-gray-600">
            <th class="hidden px-2.5 py-3 font-normal md:table-cell">Name</th>
            <th class="hidden px-2.5 py-3 font-normal lg:table-cell">Owner</th>
            <th class="hidden px-2.5 py-3 font-normal md:table-cell">
              Modified
            </th>
            <th class="hidden px-2.5 py-3 font-normal lg:table-cell">Size</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entity in folderContents"
            :id="entity.name"
            :key="entity.name"
            class="group select-none text-base shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-200 entity"
            :class="
              selectedEntities.includes(entity)
                ? 'bg-gray-100'
                : 'hover:bg-gray-50'
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
            <td class="min-w-[15rem] px-2.5 py-3 lg:w-3/6" :draggable="false">
              <div
                class="flex items-center text-gray-900 text-[14px] font-medium truncate"
                :draggable="false">
                <svg
                  v-if="entity.is_group"
                  :style="{ fill: entity.color }"
                  :draggable="false"
                  class="h-[21px] mr-5"
                  viewBox="0 0 46 40"
                  fill="#32a852"
                  xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M0.368197 17.3301C0.17175 15.5535 1.56262 14.0004 3.35002 14.0004H42.65C44.4374 14.0004 45.8283 15.5535 45.6318 17.3301L43.7155 34.6599C43.3794 37.6999 40.8104 40.0004 37.7519 40.0004H8.24812C5.18961 40.0004 2.62062 37.6999 2.28447 34.6599L0.368197 17.3301Z" />
                  <path
                    d="M43.125 11V9C43.125 6.79086 41.3341 5 39.125 5H20.312C20.1914 5 20.0749 4.95643 19.9839 4.8773L14.6572 0.245394C14.4752 0.0871501 14.2422 0 14.001 0H6.87501C4.66587 0 2.87501 1.79086 2.87501 4V11C2.87501 11.5523 3.32272 12 3.87501 12H42.125C42.6773 12 43.125 11.5523 43.125 11Z" />
                </svg>
                <img
                  v-else
                  :src="getIconUrl(formatMimeType(entity.mime_type))"
                  :draggable="false"
                  class="h-[21px] mr-5" />
                {{ entity.title }}
              </div>
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal lg:table-cell lg:w-1/6 text-gray-700">
              {{ entity.owner }}
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal md:table-cell lg:w-1/6 text-gray-700">
              {{ entity.modified }}
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal lg:table-cell lg:w-1/6 text-gray-700">
              {{ entity.file_size }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      id="selectionElement"
      class="h-20 w-20 absolute border border-blue-700 bg-blue-100 opacity-50 mix-blend-multiply"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1" />
  </div>
</template>
<script>
import { formatMimeType } from "@/utils/format";
import getIconUrl from "@/utils/getIconUrl";
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect";

export default {
  name: "GridView",
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

    this.selectAllListener = (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "a" || e.key === "A"))
        this.$emit("entitySelected", this.folderContents);
    };

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
    getFileSubtitle(file) {
      let fileSubtitle = formatMimeType(file.mime_type);
      fileSubtitle =
        fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1);
      return `${fileSubtitle} ∙ ${file.modified}`;
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
      this.$store.commit("setEntityInfo", entity);
      this.$emit("showEntityContext", { x: event.clientX, y: event.clientY });
    },
    dragStart(entity, event) {
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.effectAllowed = "move";
      // for when a user directly drags a single file
      if (this.selectedEntities.length === 0) {
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
