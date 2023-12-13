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
    :entity="
      $route.name === 'Folder'
        ? $store.state?.currentFolder
        : $store.state?.entityInfo[0]
    "
    @success="
      () => {
        showRenameDialog = false;
        $resources.getUpdatedEntityTitle.fetch();
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

  watch: {
    currentTitle: {
      handler(value) {
        document.title = value;
      },
    },
  },

  computed: {
    breadcrumbLinks() {
      return this.$store.state.currentBreadcrumbs;
    },
    currentTitle: {
      get() {
        return this.breadcrumbLinks[this.breadcrumbLinks.length - 1].label;
      },
      set(newValue) {
        return (this.breadcrumbLinks[this.breadcrumbLinks.length - 1].label =
          newValue);
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
        this.$store.state.currentFolder.owner === "Me";
        return (this.showRenameDialog = true);
      } else if (
        (this.$store.state.entityInfo[0]?.owner === "Me") |
        (this.$store.state.entityInfo[0]?.write === 1)
      ) {
        return (this.showRenameDialog = true);
      }
    },
  },
  resources: {
    getUpdatedEntityTitle() {
      return {
        url: "drive.api.files.get_title",
        params: {
          entity_name: this.currentEntityName,
          fields: "title",
        },
        onSuccess(data) {
          this.currentTitle = data;
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
      };
    },
  },
};
</script>
