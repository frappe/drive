<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div
      v-else
      ref="container"
      class="h-full my-8 px-5 md:px-0"
      @mousedown="(event) => handleMousedown(event)">
      <div v-if="folders.length > 0" class="mt-3">
        <div class="text-gray-600 font-medium">Folders</div>
        <div class="flex flex-row flex-wrap gap-5 mt-4">
          <div
            v-for="folder in folders"
            :id="folder.name"
            :key="folder.name"
            class="md:w-[212px] rounded-lg border group select-none entity"
            draggable="true"
            :class="
              selectedEntities.includes(folder)
                ? 'bg-blue-100'
                : 'hover:bg-blue-50'
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
            <div class="h-28 md:h-32 place-items-center grid">
              <img
                :src="setFolderIcon(folder.title)"
                class="h-14"
                :draggable="false" />
            </div>
            <div class="px-3.5 md:h-16 content-center grid">
              <h3 class="truncate text-[14px] font-medium">{{ folder.title }}</h3>
              <div
                class="truncate text-sm text-gray-600 flex mt-1 place-items-center">
                <img
                  :src="setFolderIcon(folder.title)"
                  class="h-3.5 mr-1.5" />
                <p>{{ folder.title }}</p>
                <p class="ml-2"> {{ folder.modified }}</p>
              </div>
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
            class="md:w-[212px] rounded-lg border group select-none entity"
            draggable="true"
            :class="
              selectedEntities.includes(file)
                ? 'bg-blue-100'
                : 'hover:bg-blue-50'
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
            <div class="h-28 md:h-32 place-items-center grid">
              <img
                :src="getIconUrl(formatMimeType(file.mime_type))"
                class="h-14"
                :draggable="false" />
            </div>
            <div class="px-3.5 md:h-16 content-center grid">
              <h3 class="truncate text-[14px] font-medium">{{ file.title }}</h3>
              <div
                class="truncate text-sm text-gray-600 flex mt-1 place-items-center">
                <img
                  :src="getIconUrl(formatMimeType(file.mime_type))"
                  class="h-3.5 mr-1.5" />
                <p>{{ getFileSubtitle(file) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      id="selectionElement"
      class="h-20 w-20 absolute border border-blue-700 bg-blue-100 opacity-50 mix-blend-multiply"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1" />
    </div>
     

</template>

<script>
import _ from 'lodash';
import { formatMimeType } from "@/utils/format";
import getIconUrl from "@/utils/getIconUrl";
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect";
import ImagesFolderImage from "@/assets/images/icons/ImagesFolder.jpg";
import VeidosFolderImage from "@/assets/images/icons/vediosFolder.png";
import GeneralFolderImage from "@/assets/images/icons/Generalfolder.png";
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
    setFolderIcon: _.memoize(function(folderTitle) {
      const typeKeywords = {
        images: ["photo", "picture", "image", "screenshot"],
        videos: ["video", "audio"]
      };
      for (const [type, keywords] of Object.entries(typeKeywords)) {
        const regex = new RegExp(`\\b(${keywords.join("|")})s?\\b`, "i");
        if (regex.test(folderTitle)) {
          return type === "images" ? ImagesFolderImage : VeidosFolderImage;
        }
      }
      return GeneralFolderImage;
    }, _.identity)

    ,
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
