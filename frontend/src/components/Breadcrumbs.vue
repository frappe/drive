<template>
  <div class="flex justify-items-center items-center text-base">
    <template v-if="dropDownItems.length">
      <Dropdown class="h-7" :options="dropDownItems">
        <Button variant="ghost">
          <template #icon>
            <svg
              class="w-4 text-gray-600"
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round">
              <circle cx="12" cy="12" r="1" />
              <circle cx="19" cy="12" r="1" />
              <circle cx="5" cy="12" r="1" />
            </svg>
          </template>
        </Button>
      </Dropdown>
      <span class="ml-1 mr-0.5 text-base text-gray-500" aria-hidden="true">
        /
      </span>
    </template>
    <router-link
      v-for="(item, index) in crumbs"
      :key="item.label"
      v-slot="{ href, navigate }"
      class="text-md line-clamp-1 sm:text-lg font-medium text-gray-600"
      :to="item.route">
      <a
        v-if="!isLastItem(index)"
        :class="[
          breadcrumbLinks.length === 1 || isLastItem(index)
            ? 'text-black'
            : ' hover:text-gray-800',
        ]"
        :href="href"
        @click="navigate">
        {{ item.label }}
        <span v-if="crumbs.length > 1" class="text-gray-600 pr-1">
          {{ "/" }}
        </span>
      </a>
      <span v-else class="text-black" @click="canShowRenameDialog">
        {{ currentTitle }}
      </span>
    </router-link>
  </div>
  <RenameDialog
    v-if="showRenameDialog"
    v-model="showRenameDialog"
    :entity="entity"
    @success="
      (data) => {
        showRenameDialog = false;
        currentTitle = data.title;
      }
    " />
</template>
<script>
import RenameDialog from "@/components/RenameDialog.vue";
import { Dropdown } from "frappe-ui";

export default {
  name: "Breadcrumbs",
  components: { RenameDialog, Dropdown },
  data() {
    return {
      title: "",
      oldTitle: "",
      showRenameDialog: false,
    };
  },
  computed: {
    entity() {
      return this.$route.name === "Folder"
        ? this.$store.state.currentFolder[0]
        : this.$store.state.entityInfo[0];
    },
    breadcrumbLinks() {
      return this.$store.state.currentBreadcrumbs;
    },
    currentTitle: {
      get() {
        let value = this.breadcrumbLinks[this.breadcrumbLinks.length - 1].label;
        if (this.$route.name === "Document") {
          value =
            value != this.$store.state.entityInfo[0]?.title
              ? this.$store.state.entityInfo[0]?.title
              : value;
        }
        document.title = value;
        return value;
      },
      set(newValue) {
        let currentBreadcrumbs = this.breadcrumbLinks;
        let updatedBreadcrumb = (currentBreadcrumbs[
          currentBreadcrumbs.length - 1
        ].label = newValue);
        this.$store.commit("setCurrentBreadcrumbs", currentBreadcrumbs);
        return newValue;
      },
    },
    currentRoute() {
      return this.breadcrumbLinks[this.breadcrumbLinks.length - 1].route;
    },
    currentEntityName() {
      return this.currentRoute.split("/")[2];
    },
    dropDownItems() {
      if (window.innerWidth > 640) return [];
      let allExceptLastTwo = this.breadcrumbLinks.slice(0, -1);
      return allExceptLastTwo.map((item) => {
        let onClick = item.onClick
          ? item.onClick
          : () => this.$router.push(item.route);
        return {
          ...item,
          icon: null,
          label: item.label,
          onClick,
        };
      });
    },
    crumbs() {
      if (window.innerWidth > 640) return this.breadcrumbLinks;

      let lastTwo = this.breadcrumbLinks.slice(-1);
      return lastTwo;
    },
  },
  methods: {
    isLastItem(index) {
      return this.breadcrumbLinks.length > 1
        ? index === this.breadcrumbLinks.length - 1
        : false;
    },
    canShowRenameDialog() {
      if (this.$route.name === "Folder") {
        if (
          (this.$store.state.currentFolder[0]?.owner === "Me") |
          this.$store.state.currentFolder[0]?.write
        ) {
          return (this.showRenameDialog = true);
        }
      } else if (
        (this.$store.state.entityInfo[0]?.owner === "Me") |
        (this.$store.state.entityInfo[0]?.write === 1)
      ) {
        return (this.showRenameDialog = true);
      }
    },
  },
};
</script>
