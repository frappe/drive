<template>
  <div v-on-outside-click="closePopup" :class="div0Class">
    <div :class="divClass">
      <Input
        v-model="search"
        icon-left="search"
        type="text"
        :class="{ 'bg-white focus:bg-white': isOpen }"
        placeholder="Search"
        @focus="openPopup"
        @input="($event) => (search = $event)" />
      <div v-if="isOpen" >

        <div class="my-2 grid gap-2 grid-cols-2 border shadow-md p-2 rounded-2xl max-w-[50%]">
          <div
            v-for="by in filterBy"
            :key="by"
            class="w-25 border rounded-lg flex flex-row cursor-pointer"
            :class="{ 'bg-gray-300': selectedFilterBy[by.imgSrc] }"
            @click="filteredBy()">
            <div class="md:flex grow items-center">
              <img :src="getIconUrl(by.imgSrc)" class="h-[22px] my-2 ml-2" />
              <div class="text-sm text-gray-700 text-center my-2 ml-2">
                {{ by.title }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="showEntities" class="overflow-y-scroll max-h-80">
          <div
            v-for="entity in filteredEntities"
            :key="entity"
            class="md:flex flex-row cursor-pointer hover:bg-gray-200 rounded-xl py-2 px-3"
            @click="openEntity(entity)">
            <div class="md:flex grow items-center">
              <img
                :src="
                  getIconUrl(
                    entity.is_group ? 'folder' : formatMimeType(entity.mime_type)
                  )
                "
                class="w-6 mr-4" />
              <div>
                <div class="text-lg text-gray-900 font-medium truncate">
                  {{ entity.title }}
                </div>
                <div v-if="selectedFilterBy['tag'] && entity.tags.length">
                  <span v-for="tag in entity.tags" :key="tag" >
                    <Badge :color="tag.color" > {{ `• ${tag.title}` }} </Badge>
                  </span>
                </div>
                <div v-else class="text-[13px] text-gray-600">{{ entity.owner }}</div>
              </div>
            </div>
            <div class="text-[13px] text-gray-600 whitespace-nowrap my-auto">
              {{ entity.modified }}
            </div>
          </div>
        </div>

        <div v-else class="grid gap-2 grid-cols-3 grid-rows-2 md:grid-cols-6 md:grid-rows-1">
          <div
            v-for="item in filterItems"
            :key="item"
            class="w-25 border rounded-lg flex flex-col cursor-pointer"
            :class="{ 'bg-gray-200': selectedFilterItems[item.imgSrc] }"
            @click="
              selectedFilterItems[item.imgSrc] = !selectedFilterItems[item.imgSrc]
            ">
            <img :src="getIconUrl(item.imgSrc)" class="h-[22px] mt-3.5 mb-3" />
            <div class="text-sm text-gray-700 text-center mb-2">
              {{ item.title }}
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
<script>
import { Input, Badge } from "frappe-ui"
import { formatSize, formatDate } from "@/utils/format";
import getFilteredEntities from "../utils/fuzzySearcher";
import { formatMimeType } from "@/utils/format";
import getIconUrl from "@/utils/getIconUrl";

export default {
  name: "SearchPopup",
  components: {
    Input, Badge,
  },
  emits: ["openEntity"],
  setup() {
    return { formatMimeType, getIconUrl };
  },
  data() {
    return {
      search: "",
      isOpen: false,
      filterItems: [
        {
          title: "Documents",
          imgSrc: "doc",
        },
        {
          title: "Spreadsheets",
          imgSrc: "spreadsheet",
        },
        {
          title: "PDFs",
          imgSrc: "pdf",
        },
        {
          title: "Image",
          imgSrc: "image",
        },
        {
          title: "Video",
          imgSrc: "video",
        },
        {
          title: "Folder",
          imgSrc: "folder",
        },
      ],
      selectedFilterItems: {
        doc: true,
        spreadsheet: true,
        pdf: true,
        image: true,
        video: true,
        folder: true,
        fullSelection: function() { 
          return (this.doc && this.spreadsheet && this.pdf && this.image && this.video && this.folder);
        },
      },
      filterBy: [
        {
          title: "Title",
          imgSrc: "unknown",
        },
        {
          title: "Tag",
          imgSrc: "tag",
        },
      ],
      selectedFilterBy: {
        unknown: true,
        tag: false,
      },
    };
  },
  computed: {
    div0Class() {
      if (!this.isOpen)
        return "w-[100px] md:w-[200px]";
      return "w-[120px] md:w-[500px] lg:w-[620px]";
    },
    divClass() {
      if (!this.isOpen)
        return "w-[100px] md:w-[200px] rounded-lg bg-white transition-all duration-[600ms]";
      return "w-[280px] md:w-[620px] mt-8 lg:mt-0 place-self-center border shadow-md p-2 rounded-2xl bg-white transition-all duration-[600ms]";
    },
    userId() {
      return this.$store.state.auth.user_id;
    },
    filteredEntities() {
      if (this.selectedFilterBy['tag']) {
        return this.prefilter;
      }
      if (this.selectedFilterItems.fullSelection()) {
        return getFilteredEntities(this.search, this.$resources.entities.data);
      } else {
        return getFilteredEntities(this.search, this.prefilter);
      }
    },
    prefilter() {
      return this.$resources.entities.data
        .filter((t) => (
          ((t.is_group && this.selectedFilterItems["folder"]) || 
            ((!t.is_group) && 
              ((this.selectedFilterItems["doc"] && t.mime_type.search(/text/) > -1)
                || (this.selectedFilterItems["spreadsheet"] && t.mime_type.search(/vnd/) > -1)
                || (this.selectedFilterItems["pdf"] && t.mime_type.search(/pdf/) > -1 ) 
                || (this.selectedFilterItems["image"] && t.mime_type.search(/image/) > -1) 
                || (this.selectedFilterItems["video"] && t.mime_type.search(/video/) > -1) 
              )
            )
          ) && 
          ((!this.selectedFilterBy['tag']) || 
            t.strtags.search("#" + this.search.toLowerCase()) > -1
          )
        ));
    },
    showEntities() {
      return this.search.length > 0;
    },
  },
  methods: {
    openEntity(entity) {
      this.isOpen = false;
      let folder = this.$resources.entities.data.filter((t) => (t.name === entity.parent_drive_entity));
      if (folder[0].is_group) {this.$emit("openEntity", folder[0]);}
      this.$emit("openEntity", entity);
    },
    openPopup() {
      this.$resources.entities.fetch();
      this.isOpen = true;
    },
    closePopup() {
      this.isOpen = false;
    },
    filteredBy() {
      this.selectedFilterBy['tag'] = !this.selectedFilterBy['tag'];
      this.selectedFilterBy['unknown'] = !this.selectedFilterBy['unknown'];
    },
  },
  resources: {
    entities() {
      return {
        url: "drive.api.permissions.get_all_my_entities",
        params: { 
          fields: ['name', 'title', 'is_group','owner', 'modified', 'file_size', 'mime_type', 'tags',
          'parent_drive_entity', ] 
        },
        onSuccess(data) {
          this.$resources.entities.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? "-"
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "me" : entity.owner;
            entity.strtags = "";
            for (let i = 0; i < entity.tags.length; i++) {
              entity.strtags += '#' + entity.tags[i]['title'].toLowerCase();
            }
          });
        },
      };
    },
  },
};
</script>
