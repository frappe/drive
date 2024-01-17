<template>
  <div class="flex justify-items-center items-center text-base">
    <router-link
      v-for="(item, index) in breadcrumbLinks"
      :key="item.label"
      v-slot="{ href, navigate }"
      class="text-lg font-medium text-gray-600"
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
        <span v-if="breadcrumbLinks.length > 1" class="text-gray-600 pr-1">
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

export default {
  name: "Breadcrumbs",
  components: { RenameDialog },
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
            value != this.$store.state.entityInfo[0].title
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
