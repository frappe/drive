<template>
  <Dialog v-model:open="open" :options="{ size: 'xl', position: 'top' }">
    <template #body>
      <div class="flex px-4 py-2 gap-1 items-center">
        <FeatherIcon class="w-4 h-auto" name="search" />
        <input
          @input="(event) => inputHandler(event.target.value)"
          icon-left="search"
          type="text"
          class="appearance-none forced-colors:hidden w-full border-none bg-transparent py-3 pl-11.5 pr-4.5 text-base text-gray-800 placeholder-gray-500 focus:ring-0"
          placeholder="Search" />
      </div>
      <div
        v-if="$resources.entities.data?.length"
        class="flex flex-col border-t px-4 overflow-y-auto overflow-x-auto max-h-[40vh] pt-2 pb-4">
        <div
          @click="openEntity(entity)"
          v-for="entity in $resources.entities.data"
          class="flex gap-2 w-full items-center rounded px-2 py-2 text-base cursor-pointer hover:bg-gray-100">
          <svg
            v-if="entity.is_group"
            class="h-auto w-5"
            :draggable="false"
            :style="{ fill: entity.color }"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg">
            <g clip-path="url(#clip0_1942_59507)">
              <path
                d="M7.83412 2.88462H1.5C1.22386 2.88462 1 3.10847 1 3.38462V12.5C1 13.6046 1.89543 14.5 3 14.5H13C14.1046 14.5 15 13.6046 15 12.5V2C15 1.72386 14.7761 1.5 14.5 1.5H9.94008C9.88623 1.5 9.83382 1.51739 9.79065 1.54957L8.13298 2.78547C8.04664 2.84984 7.94182 2.88462 7.83412 2.88462Z" />
            </g>
            <defs>
              <clipPath id="clip0_1942_59507">
                <rect width="16" height="16" fill="white" />
              </clipPath>
            </defs>
          </svg>
          <img
            v-else
            class="w-5.5 h-auto"
            :src="getIconUrl(formatMimeType(entity.mime_type))" />
          <span class="truncate w-1/2">{{ entity.title }}</span>
          <span class="ml-auto">{{ entity.owner }}</span>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, FeatherIcon, Input } from "frappe-ui";
import { formatMimeType } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";

export default {
  name: "SearchPopup",
  components: {
    Input,
    Dialog,
    FeatherIcon,
  },
  emits: ["openEntity"],
  setup() {
    return { formatMimeType, getIconUrl };
  },
  computed: {
    fullName() {
      return this.$store.state.user.fullName;
    },
    open: {
      get() {
        return this.open;
      },
      set(value) {
        this.$emit("update:open", value);
        if (!value) {
          this.newName = "";
          this.errorMessage = "";
        }
      },
    },
  },
  data() {
    return {
      isOpen: false,
      search: "",
      selectedEntity: "",
    };
  },
  methods: {
    openEntity(entity) {
      this.$resources.upwardPath
        .fetch({
          entity_name: entity.name,
        })
        .then(() => {
          if (entity.is_group) {
            this.selectedEntities = [];
            this.$router.push({
              name: "Folder",
              params: { entityName: entity.name },
            });
          } else if (entity.document) {
            this.$router.push({
              name: "Document",
              params: { entityName: entity.name },
            });
          } else {
            this.$router.push({
              name: "File",
              params: { entityName: entity.name },
            });
          }
        });
      this.emitter.emit("showSearchPopup", false);
    },
    inputHandler(value) {
      if (value.length >= 3) {
        this.search = value;
        this.$resources.entities.submit({
          query: value,
        });
      } else {
        this.$resources.entities.reset();
      }
    },
  },
  resources: {
    entities() {
      return {
        auto: false,
        method: "POST",
        url: "drive.api.files.search",
      };
    },
    upwardPath() {
      return {
        auto: false,
        method: "POST",
        url: "drive.api.files.generate_upward_path",
        onSuccess(data) {
          data.reverse();
          this.currentBreadcrumbs = [];
          data.forEach((item, depth) => {
            if (depth === 0) {
              const includesUser = item.path
                .toLowerCase()
                .includes(this.fullName.toLowerCase());
              const includesDrive = item.path
                .toLowerCase()
                .includes("drive".toLowerCase());

              if (includesUser && includesDrive) {
                this.currentBreadcrumbs.push({ label: "Home", route: "/home" });
              } else {
                this.currentBreadcrumbs.push({
                  label: "Shared",
                  route: "/shared",
                });
              }
            } else if (
              data.length > 2 &&
              depth !== data.length - 1 &&
              this.currentBreadcrumbs[0].label !== "Shared"
            ) {
              this.currentBreadcrumbs.push({
                label: item.path,
                route: "/folder/" + item.name,
              });
            }
          });
          this.$store.commit("setCurrentBreadcrumbs", this.currentBreadcrumbs);
        },
      };
    },
  },
};
</script>

<style scoped>
input {
  all: unset;
}
input:focus {
  all: unset;
  outline: none;
  border: none;
}
</style>
