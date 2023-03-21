<template>
  <div v-on-outside-click="closePopup" :class="divClass">
    <Input
      v-model="search"
      icon-left="search"
      type="text"
      :class="{ 'bg-white focus:bg-white': isOpen }"
      placeholder="Search"
      @focus="openPopup"
      @input="($event) => (search = $event)" />
    <div v-if="isOpen" class="mt-3">
      <div
        v-if="showEntities"
        v-for="entity in filteredEntities"
        :key="entity"
        class="flex flex-row cursor-pointer hover:bg-gray-100 rounded-xl py-2 px-3"
        @click="openEntity(entity)">
        <div class="flex grow items-center">
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
            <div class="text-[13px] text-gray-600">{{ entity.owner }}</div>
          </div>
        </div>
        <div class="text-[13px] text-gray-600 whitespace-nowrap my-auto">
          {{ entity.modified }}
        </div>
      </div>
      <div v-else class="mx-2.5 mb-2.5 mt-6 space-x-2.5 flex">
        <div
          v-for="item in filterItems"
          :key="item"
          class="w-28 border rounded-lg flex flex-col cursor-pointer"
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
</template>
<script>
import { Input } from "frappe-ui";
import { formatSize, formatDate } from "@/utils/format";
import getFilteredEntities from "../utils/fuzzySearcher";
import { formatMimeType } from "@/utils/format";
import getIconUrl from "@/utils/getIconUrl";

export default {
  name: "SearchPopup",
  components: {
    Input,
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
          title: "Video",
          imgSrc: "video",
        },
        {
          title: "Folder",
          imgSrc: "folder",
        },
      ],
      selectedFilterItems: {
        doc: false,
        spreadsheet: false,
        pdf: false,
        video: false,
        folder: false,
      },
    };
  },
  computed: {
    divClass() {
      if (!this.isOpen)
        return "w-[200px] rounded-lg bg-white transition-all duration-[600ms]";
      return "w-[620px] border shadow-md p-2 rounded-2xl bg-white transition-all duration-[600ms]";
    },
    userId() {
      return this.$store.state.auth.user_id;
    },
    filteredEntities() {
      return getFilteredEntities(this.search, this.$resources.entities.data);
    },
    showEntities() {
      return this.search.length > 0;
    },
  },
  methods: {
    openEntity(entity) {
      this.isOpen = false;
      this.$emit("openEntity", entity);
    },
    openPopup() {
      this.$resources.entities.fetch();
      this.isOpen = true;
    },
    closePopup() {
      this.isOpen = false;
    },
  },
  resources: {
    entities() {
      return {
        url: "drive.api.permissions.get_all_my_entities",
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
          });
        },
      };
    },
  },
};
</script>
