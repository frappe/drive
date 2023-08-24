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
      <span v-else class="text-black" @click="showRenameDialog = true">
        {{ currentTitle }}
      </span>
    </router-link>
  </div>
  <RenameDialog
    v-model="showRenameDialog"
    :entity="{
      name: currentEntityName,
      title: currentTitle,
      is_group: $route.name === 'Folder' ? 1 : 0,
    }"
    @success="
      () => {
        showRenameDialog = false;
        $resources.getUpdatedEntityTitle.fetch();
      }
    " />
</template>
<script>
import { useTitle } from "@vueuse/core";
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
    title: {
      handler(value) {
        useTitle(value);
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
  },
  resources: {
    getUpdatedEntityTitle() {
      return {
        url: "drive.api.files.get_entity",
        params: {
          entity_name: this.currentEntityName,
          fields: "title",
        },
        onSuccess(data) {
          this.currentTitle = data.title;
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
